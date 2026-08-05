/** P003.5 — Human-readable qualification receipt formatter. */
export function formatQualificationReceipt(receipt) {
  const lines = [
    "P003.5 INSTALLATION AND OFFLINE QUALIFICATION",
    "=".repeat(72),
    `Qualification: ${receipt.qualificationId}`,
    `Status: ${receipt.status}`,
    `Application version: ${receipt.applicationVersion}`,
    `Cache version: ${receipt.cacheVersion}`,
    `Database writes performed: ${receipt.databaseWritesPerformed}`,
    "",
    "FINDINGS"
  ];
  for (const finding of receipt.findings) lines.push(`- ${finding.passed ? "PASS" : "FAIL"} ${finding.code}: ${finding.message}`);
  lines.push("", "MANUAL EVIDENCE", `- Installation observed: ${receipt.manualEvidence.installationObserved}`, `- Offline reload observed: ${receipt.manualEvidence.offlineReloadObserved}`);
  return lines.join("\n");
}
