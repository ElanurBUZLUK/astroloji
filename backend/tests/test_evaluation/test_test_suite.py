"""
Tests for test suite system
"""
import pytest
from unittest.mock import Mock, AsyncMock
from app.evaluation.test_suite import TestSuite, TestCase, TestResult, TestStatus

@pytest.fixture
def mock_rag_system():
    """Mock RAG system for testing"""
    mock = Mock()
    mock.query = AsyncMock(return_value={
        "answer": "Almuten figuris is the strongest planet in essential dignity",
        "sources": [
            {"content": "Traditional astrology uses almuten calculations", "score": 0.9},
            {"content": "Essential dignity determines planetary strength", "score": 0.8}
        ],
        "citations": [{"title": "Traditional Astrology", "credibility": 0.9}]
    })
    return mock

@pytest.fixture
def mock_interpretation_engine():
    """Mock interpretation engine for testing"""
    mock = Mock()
    mock.generate_interpretation = AsyncMock(return_value={
        "interpretation": "Your Mercury almuten indicates strong communication skills",
        "confidence": 0.85,
        "coherence_score": 0.82
    })
    return mock

@pytest.mark.asyncio
async def test_test_suite_initialization():
    """Test test suite initialization"""
    test_suite = TestSuite()
    
    # Should have default test cases
    assert len(test_suite.test_cases) > 0
    
    # Should have different categories
    categories = {tc.category for tc in test_suite.test_cases}
    assert "rag" in categories
    assert "interpretation" in categories
    assert "integration" in categories

@pytest.mark.asyncio
async def test_run_rag_test_basic_query(mock_rag_system):
    """Test basic RAG query test"""
    test_suite = TestSuite()
    
    # Get basic query test case
    basic_test = next(tc for tc in test_suite.test_cases if tc.id == "rag_basic_query")
    
    # Run the test
    result = await test_suite.run_test_case(basic_test, mock_rag_system)
    
    # Should pass
    assert result.status == TestStatus.PASSED
    assert result.score > 0.5
    assert len(result.metrics) > 0

@pytest.mark.asyncio
async def test_run_rag_test_complex_query(mock_rag_system):
    """Test complex RAG query test"""
    test_suite = TestSuite()
    
    # Get complex query test case
    complex_test = next(tc for tc in test_suite.test_cases if tc.id == "rag_complex_zr_query")
    
    # Run the test
    result = await test_suite.run_test_case(complex_test, mock_rag_system)
    
    # Should have results
    assert result.status in [TestStatus.PASSED, TestStatus.FAILED]
    assert len(result.metrics) > 0

@pytest.mark.asyncio
async def test_run_interpretation_test_natal_chart(mock_interpretation_engine):
    """Test natal chart interpretation test"""
    test_suite = TestSuite()
    
    # Get natal chart test case
    natal_test = next(tc for tc in test_suite.test_cases if tc.id == "interpretation_natal_chart")
    
    # Run the test
    result = await test_suite.run_test_case(natal_test, mock_interpretation_engine)
    
    # Should have results
    assert result.status in [TestStatus.PASSED, TestStatus.FAILED]
    assert result.score >= 0
    assert len(result.metrics) > 0

@pytest.mark.asyncio
async def test_run_integration_test(mock_rag_system, mock_interpretation_engine):
    """Test full integration test"""
    test_suite = TestSuite()
    
    # Get integration test case
    integration_test = next(tc for tc in test_suite.test_cases if tc.id == "integration_full_pipeline")
    
    # Mock both systems
    systems = {
        "rag_system": mock_rag_system,
        "interpretation_engine": mock_interpretation_engine
    }
    
    # Run the test
    result = await test_suite.run_test_case(integration_test, systems)
    
    # Should have results
    assert result.status in [TestStatus.PASSED, TestStatus.FAILED]
    assert len(result.metrics) > 0

@pytest.mark.asyncio
async def test_run_all_tests(mock_rag_system, mock_interpretation_engine):
    """Test running all test cases"""
    test_suite = TestSuite()
    
    # Mock systems
    systems = {
        "rag_system": mock_rag_system,
        "interpretation_engine": mock_interpretation_engine
    }
    
    # Run all tests
    results = await test_suite.run_all_tests(systems)
    
    # Should have results for all test cases
    assert len(results) == len(test_suite.test_cases)
    
    # All results should have valid status
    for result in results:
        assert result.status in [TestStatus.PASSED, TestStatus.FAILED, TestStatus.ERROR]

@pytest.mark.asyncio
async def test_run_tests_by_category(mock_rag_system):
    """Test running tests by category"""
    test_suite = TestSuite()
    
    # Run only RAG tests
    results = await test_suite.run_tests_by_category("rag", mock_rag_system)
    
    # Should only have RAG test results
    rag_test_count = len([tc for tc in test_suite.test_cases if tc.category == "rag"])
    assert len(results) == rag_test_count
    
    # All results should be from RAG tests
    for result in results:
        test_case = next(tc for tc in test_suite.test_cases if tc.id == result.test_case_id)
        assert test_case.category == "rag"

def test_test_case_creation():
    """Test test case creation"""
    test_case = TestCase(
        id="test_case_1",
        name="Test Case 1",
        description="A test case",
        category="test",
        expected_metrics=["faithfulness", "coherence"],
        test_data={"query": "test query"}
    )
    
    assert test_case.id == "test_case_1"
    assert test_case.name == "Test Case 1"
    assert test_case.category == "test"
    assert "faithfulness" in test_case.expected_metrics

def test_test_result_creation():
    """Test test result creation"""
    from datetime import datetime
    from app.evaluation.metrics import MetricResult, MetricType
    
    metrics = [
        MetricResult(
            name="faithfulness",
            value=0.85,
            metric_type=MetricType.QUALITY,
            description="Test metric",
            timestamp=datetime.now()
        )
    ]
    
    result = TestResult(
        test_case_id="test_case_1",
        status=TestStatus.PASSED,
        score=0.85,
        metrics=metrics,
        execution_time=1.5,
        error_message=None
    )
    
    assert result.test_case_id == "test_case_1"
    assert result.status == TestStatus.PASSED
    assert result.score == 0.85
    assert len(result.metrics) == 1
    assert result.execution_time == 1.5

@pytest.mark.asyncio
async def test_test_error_handling():
    """Test error handling in test execution"""
    test_suite = TestSuite()
    
    # Create a test case that will cause an error
    error_test = TestCase(
        id="error_test",
        name="Error Test",
        description="Test that causes an error",
        category="test",
        expected_metrics=["faithfulness"],
        test_data={"query": "test"}
    )
    
    # Mock system that raises an exception
    mock_system = Mock()
    mock_system.query = AsyncMock(side_effect=Exception("Test error"))
    
    # Run the test
    result = await test_suite.run_test_case(error_test, mock_system)
    
    # Should have error status
    assert result.status == TestStatus.ERROR
    assert result.error_message is not None
    assert "Test error" in result.error_message

def test_get_test_summary():
    """Test test summary generation"""
    from datetime import datetime
    from app.evaluation.metrics import MetricResult, MetricType
    
    test_suite = TestSuite()
    
    # Create mock results
    results = [
        TestResult(
            test_case_id="test1",
            status=TestStatus.PASSED,
            score=0.85,
            metrics=[],
            execution_time=1.0
        ),
        TestResult(
            test_case_id="test2",
            status=TestStatus.FAILED,
            score=0.45,
            metrics=[],
            execution_time=1.5
        ),
        TestResult(
            test_case_id="test3",
            status=TestStatus.ERROR,
            score=0.0,
            metrics=[],
            execution_time=0.5,
            error_message="Test error"
        )
    ]
    
    summary = test_suite.get_test_summary(results)
    
    # Should have summary statistics
    assert summary["total_tests"] == 3
    assert summary["passed"] == 1
    assert summary["failed"] == 1
    assert summary["errors"] == 1
    assert summary["pass_rate"] == 1/3
    assert summary["avg_score"] == (0.85 + 0.45 + 0.0) / 3
    assert summary["avg_execution_time"] == (1.0 + 1.5 + 0.5) / 3

def test_filter_tests_by_tag():
    """Test filtering tests by tag"""
    test_suite = TestSuite()
    
    # Add tags to some test cases
    for tc in test_suite.test_cases:
        if "basic" in tc.name.lower():
            tc.tags = ["basic", "quick"]
        elif "complex" in tc.name.lower():
            tc.tags = ["complex", "slow"]
    
    # Filter by tag
    basic_tests = test_suite.get_tests_by_tag("basic")
    complex_tests = test_suite.get_tests_by_tag("complex")
    
    # Should have filtered correctly
    assert len(basic_tests) > 0
    assert len(complex_tests) > 0
    
    # All basic tests should have basic tag
    for test in basic_tests:
        assert "basic" in test.tags

@pytest.mark.asyncio
async def test_parallel_test_execution(mock_rag_system):
    """Test parallel test execution"""
    test_suite = TestSuite()
    
    # Get multiple test cases
    rag_tests = [tc for tc in test_suite.test_cases if tc.category == "rag"]
    
    # Run tests in parallel
    import asyncio
    tasks = [test_suite.run_test_case(tc, mock_rag_system) for tc in rag_tests[:2]]
    results = await asyncio.gather(*tasks)
    
    # Should have results for all tests
    assert len(results) == 2
    
    # All should have completed
    for result in results:
        assert result.status in [TestStatus.PASSED, TestStatus.FAILED, TestStatus.ERROR]

def test_test_case_validation():
    """Test test case validation"""
    test_suite = TestSuite()
    
    # All test cases should be valid
    for tc in test_suite.test_cases:
        assert tc.id is not None
        assert tc.name is not None
        assert tc.category is not None
        assert isinstance(tc.expected_metrics, list)
        assert isinstance(tc.test_data, dict)

@pytest.mark.asyncio
async def test_custom_test_case(mock_rag_system):
    """Test adding and running custom test case"""
    test_suite = TestSuite()
    
    # Create custom test case
    custom_test = TestCase(
        id="custom_test",
        name="Custom Test",
        description="A custom test case",
        category="custom",
        expected_metrics=["faithfulness"],
        test_data={"query": "What is a custom test?"}
    )
    
    # Add to test suite
    test_suite.add_test_case(custom_test)
    
    # Should be in test cases
    assert custom_test in test_suite.test_cases
    
    # Run the custom test
    result = await test_suite.run_test_case(custom_test, mock_rag_system)
    
    # Should have result
    assert result.test_case_id == "custom_test"
    assert result.status in [TestStatus.PASSED, TestStatus.FAILED, TestStatus.ERROR]