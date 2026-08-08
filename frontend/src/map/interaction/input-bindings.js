/** P006.1 DOM input bindings feeding one governed navigation controller. */
const KEY_PAN = 28;

export function bindMapNavigationInputs({ viewportElement, controller, windowRef = globalThis.window } = {}) {
  if (!viewportElement || !controller) throw new TypeError("viewportElement and controller are required");
  const disposers = [];
  const on = (target, type, handler, options) => {
    target?.addEventListener?.(type, handler, options);
    disposers.push(() => target?.removeEventListener?.(type, handler, options));
  };

  let drag = null;
  let pinchDistance = null;

  on(viewportElement, "pointerdown", (event) => {
    if (event.pointerType === "touch") return;
    drag = { x: event.clientX, y: event.clientY };
    viewportElement.setPointerCapture?.(event.pointerId);
  });
  on(viewportElement, "pointermove", (event) => {
    if (!drag || event.pointerType === "touch") return;
    const dx = event.clientX - drag.x;
    const dy = event.clientY - drag.y;
    drag = { x: event.clientX, y: event.clientY };
    controller.panBy(dx, dy, "pointer");
  });
  const stopDrag = () => { drag = null; };
  on(viewportElement, "pointerup", stopDrag);
  on(viewportElement, "pointercancel", stopDrag);

  on(viewportElement, "wheel", (event) => {
    event.preventDefault?.();
    controller.zoomBy(event.deltaY < 0 ? 1.18 : 1 / 1.18, "wheel");
  }, { passive: false });

  on(viewportElement, "touchstart", (event) => {
    if (event.touches?.length === 1) {
      drag = { x: event.touches[0].clientX, y: event.touches[0].clientY };
      pinchDistance = null;
    } else if (event.touches?.length === 2) {
      const [a, b] = event.touches;
      pinchDistance = Math.hypot(b.clientX - a.clientX, b.clientY - a.clientY);
      drag = null;
    }
  }, { passive: true });
  on(viewportElement, "touchmove", (event) => {
    if (event.touches?.length === 1 && drag) {
      const point = event.touches[0];
      controller.panBy(point.clientX - drag.x, point.clientY - drag.y, "touch-pan");
      drag = { x: point.clientX, y: point.clientY };
      return;
    }
    if (event.touches?.length === 2 && pinchDistance) {
      const [a, b] = event.touches;
      const nextDistance = Math.hypot(b.clientX - a.clientX, b.clientY - a.clientY);
      if (nextDistance > 0) controller.zoomBy(nextDistance / pinchDistance, "touch-pinch");
      pinchDistance = nextDistance;
    }
  }, { passive: true });
  on(viewportElement, "touchend", () => { drag = null; pinchDistance = null; }, { passive: true });

  on(viewportElement, "keydown", (event) => {
    const key = event.key;
    if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "+", "=", "-", "0", "Home"].includes(key)) event.preventDefault?.();
    if (key === "ArrowLeft") controller.panBy(KEY_PAN, 0, "keyboard");
    if (key === "ArrowRight") controller.panBy(-KEY_PAN, 0, "keyboard");
    if (key === "ArrowUp") controller.panBy(0, KEY_PAN, "keyboard");
    if (key === "ArrowDown") controller.panBy(0, -KEY_PAN, "keyboard");
    if (key === "+" || key === "=") controller.zoomBy(1.2, "keyboard");
    if (key === "-") controller.zoomBy(1 / 1.2, "keyboard");
    if (key === "0" || key === "Home") controller.reset("keyboard");
  });

  if (!viewportElement.hasAttribute?.("tabindex")) viewportElement.setAttribute?.("tabindex", "0");
  viewportElement.setAttribute?.("aria-label", "Interactive NoveGeo map. Use arrow keys to pan, plus and minus to zoom, and Home to reset.");
  if (viewportElement.style) viewportElement.style.touchAction = "none";

  return Object.freeze({ disconnect() { for (const dispose of disposers) dispose(); } });
}
