from vres_os.chunking import chunk_text


def test_chunking_is_deterministic_and_hashes():
    text = ("alpha " * 500) + "\n\n" + ("beta " * 500)
    first = chunk_text(text, target_chars=500, overlap_chars=50)
    second = chunk_text(text, target_chars=500, overlap_chars=50)
    assert first == second
    assert len(first) > 2
    assert all(c.content_hash and c.token_estimate > 0 for c in first)
