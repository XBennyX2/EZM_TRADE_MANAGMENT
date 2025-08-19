"""
Advanced Examples and Applications of Predictive Coding Neural Networks

This module provides additional examples and applications of the predictive coding
network, including image processing, sequence prediction, and anomaly detection.
"""

import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
from predictive_coding_network import PredictiveCodingNetwork, PredictiveCodingAutoencoder
import warnings
warnings.filterwarnings('ignore')


class PredictiveCodingRNN(PredictiveCodingNetwork):
    """
    Predictive coding network for sequence processing.
    Extends the basic network to handle temporal sequences.
    """
    
    def __init__(self, input_size: int, hidden_sizes: list, **kwargs):
        super().__init__([input_size] + hidden_sizes, **kwargs)
        
        # Add recurrent connections for temporal processing
        self.recurrent_weights = nn.ModuleList([
            nn.Linear(size, size) for size in hidden_sizes
        ])
        
        # Hidden states for sequences
        self.hidden_states = [torch.zeros(1, size) for size in hidden_sizes]
    
    def reset_states(self):
        """Reset hidden states for new sequences."""
        for i, size in enumerate(self.layer_sizes[1:]):
            self.hidden_states[i] = torch.zeros(1, size)
    
    def process_sequence(self, sequence: torch.Tensor) -> list:
        """Process a temporal sequence."""
        self.reset_states()
        outputs = []
        
        for t in range(sequence.shape[1]):  # Time dimension
            input_t = sequence[:, t, :]
            
            # Standard predictive coding inference
            representations, errors = self.inference(input_t)
            
            # Update hidden states with recurrent connections
            for i, (rep, hidden) in enumerate(zip(representations, self.hidden_states)):
                self.hidden_states[i] = torch.tanh(
                    rep + self.recurrent_weights[i](hidden)
                )
            
            outputs.append(representations[-1])  # Top-level representation
        
        return torch.stack(outputs, dim=1)


def create_sequence_data(n_sequences: int = 50, seq_length: int = 20, 
                        input_size: int = 10) -> torch.Tensor:
    """Create sequential data for testing RNN."""
    sequences = torch.zeros(n_sequences, seq_length, input_size)
    
    for i in range(n_sequences):
        # Create different types of sequences
        seq_type = i % 3
        
        if seq_type == 0:
            # Sine wave with different frequencies
            freq = 0.1 + 0.05 * (i % 10)
            for t in range(seq_length):
                sequences[i, t, :] = torch.sin(2 * np.pi * freq * t + torch.linspace(0, 2*np.pi, input_size))
        
        elif seq_type == 1:
            # Random walk
            walk = torch.cumsum(torch.randn(seq_length, input_size) * 0.1, dim=0)
            sequences[i] = walk
        
        else:
            # Oscillating pattern
            for t in range(seq_length):
                sequences[i, t, :] = torch.sin(t * 0.3) * torch.ones(input_size)
    
    return sequences


class PredictiveCodingAnomalyDetector(PredictiveCodingAutoencoder):
    """
    Use predictive coding for anomaly detection.
    Normal patterns have low prediction error, anomalies have high error.
    """
    
    def __init__(self, input_size: int, hidden_sizes: list, **kwargs):
        super().__init__(input_size, hidden_sizes, **kwargs)
        self.threshold = None
    
    def fit_threshold(self, normal_data: torch.Tensor, percentile: float = 95):
        """Fit threshold for anomaly detection based on normal data."""
        with torch.no_grad():
            errors = []
            for i in range(normal_data.shape[0]):
                error = self.compute_free_energy(normal_data[i:i+1])
                errors.append(error.item())
            
            self.threshold = np.percentile(errors, percentile)
            print(f"Anomaly detection threshold set to: {self.threshold:.4f}")
    
    def detect_anomalies(self, data: torch.Tensor) -> torch.Tensor:
        """Detect anomalies in data."""
        if self.threshold is None:
            raise ValueError("Must call fit_threshold first!")
        
        with torch.no_grad():
            anomaly_scores = []
            for i in range(data.shape[0]):
                error = self.compute_free_energy(data[i:i+1])
                anomaly_scores.append(error.item())
            
            anomaly_scores = torch.tensor(anomaly_scores)
            return anomaly_scores > self.threshold


def create_anomaly_data(n_normal: int = 100, n_anomalies: int = 20, 
                       data_size: int = 15) -> tuple:
    """Create normal and anomalous data for testing."""
    # Normal data: smooth patterns
    normal_data = torch.zeros(n_normal, data_size)
    for i in range(n_normal):
        # Smooth sine waves with small variations
        freq = 0.5 + 0.3 * torch.rand(1)
        phase = 2 * np.pi * torch.rand(1)
        normal_data[i] = torch.sin(freq * torch.linspace(0, 4*np.pi, data_size) + phase)
        normal_data[i] += 0.1 * torch.randn(data_size)  # Small noise
    
    # Anomalous data: spiky or very different patterns
    anomaly_data = torch.zeros(n_anomalies, data_size)
    for i in range(n_anomalies):
        if i % 2 == 0:
            # Spiky patterns
            anomaly_data[i] = torch.randn(data_size) * 2
        else:
            # Very high frequency or discontinuous patterns
            anomaly_data[i] = torch.sign(torch.sin(10 * torch.linspace(0, 4*np.pi, data_size))) * 2
    
    return normal_data, anomaly_data


def demonstrate_image_patches():
    """Demonstrate predictive coding on image patches."""
    print("Image Patch Processing Demo")
    print("-" * 30)
    
    # Create synthetic image patches (8x8 patches)
    patch_size = 64  # 8x8 = 64 pixels
    n_patches = 200
    
    patches = torch.zeros(n_patches, patch_size)
    
    for i in range(n_patches):
        # Create different types of patches
        patch_type = i % 4
        patch_2d = torch.zeros(8, 8)
        
        if patch_type == 0:
            # Horizontal lines
            patch_2d[2:6, :] = 1.0
        elif patch_type == 1:
            # Vertical lines
            patch_2d[:, 2:6] = 1.0
        elif patch_type == 2:
            # Diagonal lines
            for j in range(8):
                if j < 8:
                    patch_2d[j, j] = 1.0
        else:
            # Checkerboard pattern
            for x in range(8):
                for y in range(8):
                    if (x + y) % 2 == 0:
                        patch_2d[x, y] = 1.0
        
        patches[i] = patch_2d.flatten()
        patches[i] += 0.1 * torch.randn(patch_size)  # Add noise
    
    # Train network on patches
    network = PredictiveCodingAutoencoder(
        input_size=patch_size,
        hidden_sizes=[32, 16, 8],
        learning_rate=0.1,
        inference_steps=15
    )
    
    print(f"Training on {n_patches} image patches...")
    free_energies = network.learn(patches, num_epochs=80)
    
    # Test reconstruction
    test_patches = patches[:5]
    with torch.no_grad():
        reconstructions = network.reconstruct(test_patches)
        mse = torch.mean((test_patches - reconstructions)**2)
        print(f"Reconstruction MSE: {mse.item():.4f}")
    
    return network, patches, free_energies


def demonstrate_sequence_prediction():
    """Demonstrate sequence prediction with RNN."""
    print("\nSequence Prediction Demo")
    print("-" * 25)
    
    # Create sequence data
    sequences = create_sequence_data(n_sequences=30, seq_length=15, input_size=8)
    
    # Create RNN network
    rnn_network = PredictiveCodingRNN(
        input_size=8,
        hidden_sizes=[12, 8, 4],
        learning_rate=0.1,
        inference_steps=10
    )
    
    print(f"Training on {sequences.shape[0]} sequences...")
    
    # Train on sequences (simplified training for demo)
    optimizer = torch.optim.Adam(rnn_network.parameters(), lr=0.01)
    losses = []
    
    for epoch in range(50):
        total_loss = 0
        for seq in sequences:
            optimizer.zero_grad()
            
            # Process sequence
            outputs = rnn_network.process_sequence(seq.unsqueeze(0))
            
            # Simple prediction loss (predict next timestep)
            loss = 0
            for t in range(seq.shape[0] - 1):
                # Try to predict next input from current representation
                pred_error = torch.mean((seq[t+1] - seq[t])**2)
                loss += pred_error
            
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        losses.append(total_loss / len(sequences))
        if epoch % 10 == 0:
            print(f"Epoch {epoch}, Average Loss: {losses[-1]:.4f}")
    
    return rnn_network, sequences, losses


def demonstrate_anomaly_detection():
    """Demonstrate anomaly detection."""
    print("\nAnomaly Detection Demo")
    print("-" * 22)
    
    # Create normal and anomalous data
    normal_data, anomaly_data = create_anomaly_data(n_normal=80, n_anomalies=20)
    
    # Train detector on normal data
    detector = PredictiveCodingAnomalyDetector(
        input_size=15,
        hidden_sizes=[10, 6, 3],
        learning_rate=0.1,
        inference_steps=12
    )
    
    print("Training anomaly detector on normal data...")
    detector.learn(normal_data, num_epochs=60)
    
    # Fit threshold
    detector.fit_threshold(normal_data, percentile=95)
    
    # Test on mixed data
    test_data = torch.cat([normal_data[:10], anomaly_data[:10]], dim=0)
    true_labels = torch.cat([torch.zeros(10), torch.ones(10)])  # 0=normal, 1=anomaly
    
    predictions = detector.detect_anomalies(test_data)
    accuracy = torch.mean((predictions.float() == true_labels).float())
    
    print(f"Anomaly detection accuracy: {accuracy.item():.2f}")
    print(f"Detected {torch.sum(predictions).item()} anomalies out of {len(predictions)}")
    
    return detector, normal_data, anomaly_data


if __name__ == "__main__":
    print("Advanced Predictive Coding Examples")
    print("=" * 40)
    
    # Run demonstrations
    try:
        # Image patch processing
        img_network, patches, img_losses = demonstrate_image_patches()
        
        # Sequence prediction
        seq_network, sequences, seq_losses = demonstrate_sequence_prediction()
        
        # Anomaly detection
        detector, normal_data, anomaly_data = demonstrate_anomaly_detection()
        
        print("\n" + "=" * 40)
        print("All demonstrations completed successfully!")
        print("The predictive coding networks successfully learned:")
        print("1. Image patch representations")
        print("2. Temporal sequence patterns")
        print("3. Normal vs anomalous data patterns")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        print("Make sure all dependencies are installed.")