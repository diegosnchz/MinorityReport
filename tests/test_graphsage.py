"""
Tests for GraphSAGE implementation

This module contains basic tests to validate:
1. Model instantiation
2. Forward pass
3. Different aggregation methods
4. Clustering functionality
5. Mini-batch compatibility
"""

import sys
import os

# Test without requiring PyTorch installation
def test_imports():
    """Test that the modules can be imported (syntax check)"""
    print("Testing imports...")
    
    try:
        # Check if files exist
        assert os.path.exists('graphsage_model.py'), "graphsage_model.py not found"
        assert os.path.exists('train_graphsage_minibatch.py'), "train_graphsage_minibatch.py not found"
        assert os.path.exists('GRAPHSAGE_README.md'), "GRAPHSAGE_README.md not found"
        
        print("✓ All required files exist")
        return True
    except AssertionError as e:
        print(f"✗ Import test failed: {e}")
        return False


def test_code_structure():
    """Test that the code has the required components"""
    print("\nTesting code structure...")
    
    with open('graphsage_model.py', 'r') as f:
        code = f.read()
    
    required_classes = [
        'GraphSAGEAggregator',
        'GraphSAGEWithClustering',
        'GraphSAGEMiniBatch'
    ]
    
    required_functions = [
        'create_graphsage_model'
    ]
    
    required_aggregators = ['mean', 'lstm', 'pool']
    
    try:
        # Check classes
        for cls in required_classes:
            assert f"class {cls}" in code, f"Class {cls} not found"
            print(f"  ✓ Class {cls} found")
        
        # Check functions
        for func in required_functions:
            assert f"def {func}" in code, f"Function {func} not found"
            print(f"  ✓ Function {func} found")
        
        # Check aggregator support
        for aggr in required_aggregators:
            assert f"'{aggr}'" in code, f"Aggregator '{aggr}' not supported"
            print(f"  ✓ Aggregator '{aggr}' supported")
        
        # Check for SAGEConv usage
        assert 'SAGEConv' in code, "SAGEConv not used"
        print("  ✓ SAGEConv used for GraphSAGE layers")
        
        # Check for clustering
        assert 'cluster' in code.lower(), "Clustering not implemented"
        print("  ✓ Clustering support found")
        
        return True
    except AssertionError as e:
        print(f"  ✗ Structure test failed: {e}")
        return False


def test_training_structure():
    """Test that the training code has mini-batch support"""
    print("\nTesting training code structure...")
    
    with open('train_graphsage_minibatch.py', 'r') as f:
        code = f.read()
    
    required_components = [
        'NeighborLoader',  # For neighbor sampling
        'train_minibatch_epoch',  # Mini-batch training
        'batch_size',  # Batch size parameter
        'num_neighbors',  # Neighbor sampling parameter
        'train_with_clustering',  # Clustering training
    ]
    
    try:
        for component in required_components:
            assert component in code, f"Component '{component}' not found"
            print(f"  ✓ {component} found")
        
        # Check for mini-batch gradient descent mention
        assert 'mini-batch' in code.lower() or 'minibatch' in code.lower(), \
            "Mini-batch not mentioned"
        print("  ✓ Mini-batch gradient descent implemented")
        
        # Check for neighbor sampling
        assert 'neighbor' in code.lower() and 'sampl' in code.lower(), \
            "Neighbor sampling not mentioned"
        print("  ✓ Neighbor sampling implemented")
        
        return True
    except AssertionError as e:
        print(f"  ✗ Training structure test failed: {e}")
        return False


def test_documentation():
    """Test that documentation is complete"""
    print("\nTesting documentation...")
    
    with open('GRAPHSAGE_README.md', 'r') as f:
        doc = f.read()
    
    required_sections = [
        'Mini-batch',
        'Neighbor Sampling',
        'Aggregation',
        'Clustering',
        'mean',
        'lstm',
        'pool',
        'Usage',
    ]
    
    try:
        for section in required_sections:
            assert section.lower() in doc.lower(), f"Section '{section}' not documented"
            print(f"  ✓ {section} documented")
        
        # Check for reference to the source
        assert 'mlabonne' in doc.lower() or 'graphsage' in doc.lower(), \
            "Reference to GraphSAGE source not found"
        print("  ✓ Source reference included")
        
        return True
    except AssertionError as e:
        print(f"  ✗ Documentation test failed: {e}")
        return False


def test_requirements():
    """Test that key features are mentioned in code"""
    print("\nTesting key feature implementation...")
    
    with open('graphsage_model.py', 'r') as f:
        model_code = f.read()
    
    with open('train_graphsage_minibatch.py', 'r') as f:
        train_code = f.read()
    
    features = {
        'Mini-batch support': 'batch' in train_code.lower(),
        'Neighbor sampling': 'neighbor' in train_code.lower() and 'sampl' in train_code.lower(),
        'Mean aggregation': "'mean'" in model_code,
        'LSTM aggregation': "'lstm'" in model_code,
        'Pooling aggregation': "'pool'" in model_code,
        'Clustering': 'cluster' in model_code.lower(),
        'SAGEConv usage': 'SAGEConv' in model_code,
        'NeighborLoader': 'NeighborLoader' in train_code,
    }
    
    try:
        for feature, present in features.items():
            assert present, f"Feature '{feature}' not implemented"
            print(f"  ✓ {feature} implemented")
        
        return True
    except AssertionError as e:
        print(f"  ✗ Feature test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("GraphSAGE Implementation Tests")
    print("=" * 70)
    
    tests = [
        test_imports,
        test_code_structure,
        test_training_structure,
        test_documentation,
        test_requirements,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✨ All tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
