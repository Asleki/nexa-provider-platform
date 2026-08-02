from database.migration_control.sanitization import sanitize_text

def test_sanitizer_removes_passwords_and_uri_credentials():
    text=sanitize_text('postgresql://user:secret@host/db password=secret user=admin')
    assert 'secret' not in text and '[redacted]' in text
