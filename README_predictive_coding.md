# Predictive Coding Neural Network Implementation

A comprehensive implementation of hierarchical predictive coding neural networks inspired by neuroscience theories of brain function.

## Overview

Predictive coding is a theory of neural processing where the brain constantly generates predictions about incoming sensory data and updates these predictions based on prediction errors. This implementation provides:

- **Hierarchical Architecture**: Multiple layers that generate top-down predictions
- **Error Minimization**: Bottom-up error signals that drive learning
- **Iterative Inference**: Gradual refinement of predictions through multiple steps
- **Biologically Inspired**: Based on theories of cortical processing

## Key Features

### Core Components

1. **PredictiveCodingLayer**: Individual layer with prediction and error computation
2. **PredictiveCodingNetwork**: Multi-layer hierarchical network
3. **PredictiveCodingAutoencoder**: Specialized for reconstruction tasks
4. **PredictiveCodingRNN**: Extended for temporal sequence processing
5. **PredictiveCodingAnomalyDetector**: Anomaly detection through prediction errors

### Capabilities

- **Pattern Learning**: Learn hierarchical representations of data
- **Reconstruction**: Generate reconstructions through predictive inference
- **Sequence Processing**: Handle temporal patterns and dependencies
- **Anomaly Detection**: Identify unusual patterns through high prediction errors
- **Unsupervised Learning**: Learn without explicit labels

## Installation

```bash
pip install -r requirements_predictive_coding.txt
```

## Quick Start

### Basic Usage

```python
from predictive_coding_network import PredictiveCodingAutoencoder
import torch

# Create sample data
data = torch.randn(100, 20)  # 100 samples, 20 features

# Initialize network
network = PredictiveCodingAutoencoder(
    input_size=20,
    hidden_sizes=[15, 10, 5],
    learning_rate=0.1,
    inference_steps=20
)

# Train the network
free_energies = network.learn(data, num_epochs=100)

# Reconstruct data
with torch.no_grad():
    reconstructions = network.reconstruct(data[:5])
```

### Advanced Examples

```python
from predictive_coding_examples import *

# Image patch processing
img_network, patches, losses = demonstrate_image_patches()

# Sequence prediction
seq_network, sequences, seq_losses = demonstrate_sequence_prediction()

# Anomaly detection
detector, normal_data, anomaly_data = demonstrate_anomaly_detection()
```

## Architecture Details

### Hierarchical Structure

```
Input Layer (observations)
    ↑ errors    ↓ predictions
Layer 1 (representations)
    ↑ errors    ↓ predictions  
Layer 2 (representations)
    ↑ errors    ↓ predictions
...
Top Layer (high-level representations)
```

### Learning Process

1. **Forward Pass**: Generate predictions from higher to lower layers
2. **Error Computation**: Calculate differences between predictions and actual values
3. **Representation Update**: Adjust representations to minimize errors
4. **Parameter Update**: Update network weights to improve predictions

### Free Energy Minimization

The network minimizes "free energy" - the total prediction error across all layers:

```
Free Energy = Σ(prediction_errors²)
```

Lower free energy indicates better internal models of the data.

## Mathematical Foundation

### Prediction Generation
```
prediction_i = W_pred_i × representation_i + bias_pred_i
```

### Error Computation
```
error_i = input_i - prediction_i
```

### Representation Update
```
representation_i = tanh(W_rec_i × error_i + higher_prediction_i)
```

## Applications

### 1. Unsupervised Feature Learning
Learn hierarchical representations without labels:
```python
network = PredictiveCodingAutoencoder(input_size=784, hidden_sizes=[256, 128, 64])
features = network(mnist_data)  # Extract learned features
```

### 2. Anomaly Detection
Detect unusual patterns through high prediction errors:
```python
detector = PredictiveCodingAnomalyDetector(input_size=50, hidden_sizes=[25, 10])
detector.learn(normal_data)
detector.fit_threshold(normal_data)
anomalies = detector.detect_anomalies(test_data)
```

### 3. Sequence Modeling
Process temporal data with recurrent predictive coding:
```python
rnn = PredictiveCodingRNN(input_size=10, hidden_sizes=[20, 15, 10])
representations = rnn.process_sequence(time_series_data)
```

## Parameters

### Network Configuration
- `layer_sizes`: List defining architecture [input_size, hidden1, hidden2, ...]
- `learning_rate`: Rate of representation updates (default: 0.1)
- `inference_steps`: Number of iterative inference steps (default: 10)

### Training Parameters
- `num_epochs`: Training iterations
- `optimizer`: PyTorch optimizer (Adam recommended)

## Performance Tips

1. **Inference Steps**: More steps = better convergence but slower processing
2. **Learning Rate**: Lower rates for stable learning, higher for faster adaptation
3. **Architecture**: Gradual size reduction works well for autoencoders
4. **Initialization**: Small random weights prevent saturation

## Biological Motivation

This implementation is inspired by:

- **Predictive Processing Theory**: Brain as prediction machine
- **Hierarchical Temporal Memory**: Cortical learning algorithms
- **Free Energy Principle**: Minimization of surprise/prediction error
- **Bayesian Brain Hypothesis**: Neural inference through prediction

## Comparison with Standard Networks

| Aspect | Predictive Coding | Standard Neural Network |
|--------|------------------|------------------------|
| Learning | Error minimization | Gradient descent on loss |
| Inference | Iterative refinement | Single forward pass |
| Representations | Hierarchical predictions | Hidden activations |
| Biological Plausibility | High | Lower |
| Interpretability | High (error signals) | Lower |

## Files

- `predictive_coding_network.py`: Core implementation
- `predictive_coding_examples.py`: Advanced examples and applications
- `requirements_predictive_coding.txt`: Dependencies
- `README_predictive_coding.md`: This documentation

## References

- Friston, K. (2005). A theory of cortical responses. Philosophical Transactions of the Royal Society B.
- Rao, R. P., & Ballard, D. H. (1999). Predictive coding in the visual cortex. Nature Neuroscience.
- Clark, A. (2013). Whatever next? Predictive brains, situated agents, and the future of cognitive science.
- Hohwy, J. (2013). The predictive mind: cognitive science meets philosophy of mind.

## License

MIT License - Feel free to use and modify for research and applications.