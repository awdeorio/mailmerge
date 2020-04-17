"""
End-to-end tests with a live SMTP server.

Andrew DeOrio <awdeorio@umich.edu>
"""

def test_simple(live_smtp_server):
    """Simple, unauthenticated test."""
    print("hello world")
