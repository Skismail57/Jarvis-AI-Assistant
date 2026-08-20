import pytest


def test_add_returns_doc_id(tmp_vector_persist_dir):
    from assistant.memory.vector_memory import VectorMemory
    vm = VectorMemory(
        persist_dir=tmp_vector_persist_dir,
        collection_name="test_col",
        top_k=3,
        min_score=0.0,
    )
    doc_id = vm.add("The quick brown fox jumps over the lazy dog", memory_type="fact", user_id="alice")
    assert isinstance(doc_id, str)
    assert len(doc_id) > 0
    assert vm.count() >= 1


def test_add_conversation_pair(tmp_vector_persist_dir):
    from assistant.memory.vector_memory import VectorMemory
    vm = VectorMemory(
        persist_dir=tmp_vector_persist_dir,
        collection_name="test_col2",
        top_k=5,
        min_score=0.0,
    )
    vm.clear()
    vm.add_conversation_pair("What is Python?", "Python is a programming language.")
    vm.add_conversation_pair("What is Java?", "Java is another programming language.")
    assert vm.count() >= 2


def test_add_fact_with_tags(tmp_vector_persist_dir):
    from assistant.memory.vector_memory import VectorMemory
    vm = VectorMemory(
        persist_dir=tmp_vector_persist_dir,
        collection_name="test_col3",
        top_k=5,
        min_score=0.0,
    )
    vm.clear()
    id1 = vm.add_fact("The Eiffel Tower is in Paris.", tags=["geography", "landmarks"], source="learned")
    id2 = vm.add_fact("Water boils at 100 degrees Celsius.")
    assert isinstance(id1, str)
    assert isinstance(id2, str)
    assert vm.count() >= 2


def test_search_returns_results_with_score(tmp_vector_persist_dir):
    from assistant.memory.vector_memory import VectorMemory
    vm = VectorMemory(
        persist_dir=tmp_vector_persist_dir,
        collection_name="test_col4",
        top_k=5,
        min_score=0.0,
    )
    vm.clear()
    vm.add("Python programming language with indentation", memory_type="fact")
    vm.add("JavaScript language for web browsers", memory_type="fact")
    vm.add("C++ compiled systems language", memory_type="fact")
    results = vm.search("Python language", top_k=2)
    assert isinstance(results, list)
    for r in results:
        assert "id" in r
        assert "content" in r
        assert "metadata" in r
        assert "score" in r
        assert isinstance(r["score"], float)


def test_search_respects_top_k(tmp_vector_persist_dir):
    from assistant.memory.vector_memory import VectorMemory
    vm = VectorMemory(
        persist_dir=tmp_vector_persist_dir,
        collection_name="test_col5",
        top_k=10,
        min_score=0.0,
    )
    vm.clear()
    for i in range(8):
        vm.add(f"Data entry number {i} about apples and fruits", memory_type="fact")
    results = vm.search("apples fruits data", top_k=3)
    assert len(results) <= 3


def test_count_and_clear(tmp_vector_persist_dir):
    from assistant.memory.vector_memory import VectorMemory
    vm = VectorMemory(
        persist_dir=tmp_vector_persist_dir,
        collection_name="test_col6",
        top_k=5,
        min_score=0.0,
    )
    vm.clear()
    before = vm.count()
    for i in range(5):
        vm.add(f"Item {i} to be counted", memory_type="conversation")
    assert vm.count() >= before + 1
    vm.clear()
    assert vm.count() == 0


def test_clear_by_memory_type(tmp_vector_persist_dir):
    from assistant.memory.vector_memory import VectorMemory
    vm = VectorMemory(
        persist_dir=tmp_vector_persist_dir,
        collection_name="test_col7",
        top_k=5,
        min_score=0.0,
    )
    vm.clear()
    vm.add("Conversation 1", memory_type="conversation")
    vm.add("Conversation 2", memory_type="conversation")
    vm.add_fact("Fact one here")
    total_before = vm.count()
    vm.clear(memory_type="conversation")
    total_after = vm.count()
    assert total_after <= total_before
