"""
Predictive Coding Neural Network Implementation

This module implements a hierarchical predictive coding network inspired by 
neuroscience theories of how the brain processes information through prediction 
and error correction.

Key concepts:
- Hierarchical layers that generate predictions
- Error units that compute prediction errors
- Top-down predictions and bottom-up error signals
- Iterative inference through prediction updates
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class PredictiveCodingLayer(nn.Module):
    """
    A single layer in the predictive coding hierarchy.
    
    Each layer contains:
    - Representation units (predictions)
    - Error units (prediction errors)
    - Connections for top-down predictions and bottom-up errors
    """
    
    def __init__(self, input_size: int, hidden_size: int, learning_rate: float = 0.1):
        super(PredictiveCodingLayer, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.learning_rate = learning_rate
        
        # Prediction weights (top-down)
        self.W_pred = nn.Parameter(torch.randn(hidden_size, input_size) * 0.1)
        
        # Recognition weights (bottom-up)
        self.W_rec = nn.Parameter(torch.randn(input_size, hidden_size) * 0.1)
        
        # Biases
        self.bias_pred = nn.Parameter(torch.zeros(input_size))
        self.bias_rec = nn.Parameter(torch.zeros(hidden_size))
        
        # State variables
        self.representation = torch.zeros(1, hidden_size)
        self.prediction = torch.zeros(1, input_size)
        self.error = torch.zeros(1, input_size)
        
    def forward_prediction(self, representation: torch.Tensor) -> torch.Tensor:
        """Generate top-down prediction from representation."""
        return torch.matmul(representation, self.W_pred) + self.bias_pred
    
    def compute_error(self, input_data: torch.Tensor, prediction: torch.Tensor) -> torch.Tensor:
        """Compute prediction error."""
        return input_data - prediction
    
    def update_representation(self, error: torch.Tensor, higher_prediction: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Update representation based on error signals."""
        # Bottom-up error signal
        error_signal = torch.matmul(error, self.W_rec) + self.bias_rec
        
        # If there's a higher-level prediction, incorporate it
        if higher_prediction is not None:
            representation = higher_prediction + self.learning_rate * error_signal
        else:
            representation = self.learning_rate * error_signal
            
        return torch.tanh(representation)  # Non-linear activation


class PredictiveCodingNetwork(nn.Module):
    """
    Multi-layer predictive coding network.
    
    Implements hierarchical predictive coding with multiple layers where:
    - Higher layers generate predictions for lower layers
    - Lower layers send error signals to higher layers
    - The network iteratively minimizes prediction errors
    """
    
    def __init__(self, layer_sizes: List[int], learning_rate: float = 0.1, 
                 inference_steps: int = 10):
        super(PredictiveCodingNetwork, self).__init__()
        
        self.layer_sizes = layer_sizes
        self.learning_rate = learning_rate
        self.inference_steps = inference_steps
        self.num_layers = len(layer_sizes) - 1
        
        # Create layers
        self.layers = nn.ModuleList()
        for i in range(self.num_layers):
            layer = PredictiveCodingLayer(
                input_size=layer_sizes[i],
                hidden_size=layer_sizes[i + 1],
                learning_rate=learning_rate
            )
            self.layers.append(layer)
        
        # State variables for all layers
        self.representations = [torch.zeros(1, size) for size in layer_sizes[1:]]
        self.predictions = [torch.zeros(1, size) for size in layer_sizes[:-1]]
        self.errors = [torch.zeros(1, size) for size in layer_sizes[:-1]]
        
    def inference(self, input_data: torch.Tensor) -> Tuple[List[torch.Tensor], List[torch.Tensor]]:
        """
        Perform iterative inference to minimize prediction errors.
        
        Args:
            input_data: Input stimulus
            
        Returns:
            Tuple of (representations, errors) for all layers
        """
        batch_size = input_data.shape[0]
        
        # Initialize representations
        representations = [torch.zeros(batch_size, size) for size in self.layer_sizes[1:]]
        
        # Iterative inference
        for step in range(self.inference_steps):
            # Forward pass: generate predictions from top to bottom
            predictions = []
            for i in range(self.num_layers):
                if i == 0:
                    # Lowest layer predicts input
                    pred = self.layers[i].forward_prediction(representations[i])
                else:
                    # Higher layers predict lower representations
                    pred = self.layers[i].forward_prediction(representations[i])
                predictions.append(pred)
            
            # Compute errors
            errors = []
            for i in range(self.num_layers):
                if i == 0:
                    # Error between prediction and actual input
                    error = self.layers[i].compute_error(input_data, predictions[i])
                else:
                    # Error between prediction and lower representation
                    error = self.layers[i].compute_error(representations[i-1], predictions[i])
                errors.append(error)
            
            # Update representations based on errors
            new_representations = []
            for i in range(self.num_layers):
                if i == self.num_layers - 1:
                    # Top layer has no higher prediction
                    new_rep = self.layers[i].update_representation(errors[i])
                else:
                    # Use higher layer prediction
                    higher_pred = predictions[i+1] if i+1 < len(predictions) else None
                    new_rep = self.layers[i].update_representation(errors[i], higher_pred)
                new_representations.append(new_rep)
            
            representations = new_representations
        
        return representations, errors
    
    def forward(self, input_data: torch.Tensor) -> torch.Tensor:
        """Forward pass returning top-level representation."""
        representations, _ = self.inference(input_data)
        return representations[-1]  # Return top-level representation
    
    def compute_free_energy(self, input_data: torch.Tensor) -> torch.Tensor:
        """
        Compute free energy (total prediction error) of the network.
        Lower free energy indicates better predictions.
        """
        _, errors = self.inference(input_data)
        
        free_energy = 0.0
        for error in errors:
            free_energy += torch.sum(error ** 2)
        
        return free_energy
    
    def learn(self, input_data: torch.Tensor, num_epochs: int = 100) -> List[float]:
        """
        Train the network to minimize prediction errors.
        
        Args:
            input_data: Training data
            num_epochs: Number of training epochs
            
        Returns:
            List of free energy values during training
        """
        optimizer = torch.optim.Adam(self.parameters(), lr=0.01)
        free_energies = []
        
        for epoch in range(num_epochs):
            optimizer.zero_grad()
            
            # Compute free energy (loss)
            free_energy = self.compute_free_energy(input_data)
            
            # Backward pass
            free_energy.backward()
            optimizer.step()
            
            free_energies.append(free_energy.item())
            
            if epoch % 20 == 0:
                print(f"Epoch {epoch}, Free Energy: {free_energy.item():.4f}")
        
        return free_energies


class PredictiveCodingAutoencoder(PredictiveCodingNetwork):
    """
    Predictive coding network configured as an autoencoder.
    Learns to reconstruct inputs through hierarchical predictions.
    """
    
    def __init__(self, input_size: int, hidden_sizes: List[int], **kwargs):
        # Create symmetric architecture for autoencoder
        layer_sizes = [input_size] + hidden_sizes
        super().__init__(layer_sizes, **kwargs)
        
    def reconstruct(self, input_data: torch.Tensor) -> torch.Tensor:
        """Reconstruct input through predictive coding inference."""
        representations, errors = self.inference(input_data)
        
        # Generate reconstruction from lowest layer prediction
        reconstruction = self.layers[0].forward_prediction(representations[0])
        return reconstruction


def create_sample_data(n_samples: int = 100, pattern_size: int = 20) -> torch.Tensor:
    """Create sample data with patterns for testing."""
    data = torch.zeros(n_samples, pattern_size)
    
    # Create different patterns
    for i in range(n_samples):
        pattern_type = i % 3
        if pattern_type == 0:
            # Sine wave pattern
            data[i] = torch.sin(torch.linspace(0, 4*np.pi, pattern_size))
        elif pattern_type == 1:
            # Square wave pattern
            data[i] = torch.sign(torch.sin(torch.linspace(0, 4*np.pi, pattern_size)))
        else:
            # Random sparse pattern
            indices = torch.randperm(pattern_size)[:pattern_size//4]
            data[i, indices] = 1.0
    
    # Add noise
    data += 0.1 * torch.randn_like(data)
    
    return data


def visualize_learning(free_energies: List[float]):
    """Visualize the learning progress."""
    plt.figure(figsize=(10, 6))
    plt.plot(free_energies)
    plt.title('Predictive Coding Network Learning')
    plt.xlabel('Epoch')
    plt.ylabel('Free Energy (Prediction Error)')
    plt.grid(True)
    plt.show()


def visualize_reconstruction(original: torch.Tensor, reconstructed: torch.Tensor, 
                           num_samples: int = 5):
    """Visualize original vs reconstructed patterns."""
    fig, axes = plt.subplots(2, num_samples, figsize=(15, 6))
    
    for i in range(num_samples):
        # Original
        axes[0, i].plot(original[i].detach().numpy())
        axes[0, i].set_title(f'Original {i+1}')
        axes[0, i].grid(True)
        
        # Reconstructed
        axes[1, i].plot(reconstructed[i].detach().numpy())
        axes[1, i].set_title(f'Reconstructed {i+1}')
        axes[1, i].grid(True)
    
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Example usage and demonstration
    print("Predictive Coding Neural Network Demo")
    print("=" * 40)
    
    # Create sample data
    print("Creating sample data...")
    data = create_sample_data(n_samples=50, pattern_size=20)
    
    # Create network
    print("Initializing predictive coding network...")
    network = PredictiveCodingAutoencoder(
        input_size=20,
        hidden_sizes=[15, 10, 5],
        learning_rate=0.1,
        inference_steps=20
    )
    
    print(f"Network architecture: {network.layer_sizes}")
    print(f"Number of parameters: {sum(p.numel() for p in network.parameters())}")
    
    # Test inference before training
    print("\nTesting inference before training...")
    with torch.no_grad():
        initial_free_energy = network.compute_free_energy(data[:5])
        print(f"Initial free energy: {initial_free_energy.item():.4f}")
    
    # Train the network
    print("\nTraining network...")
    free_energies = network.learn(data, num_epochs=100)
    
    # Test reconstruction after training
    print("\nTesting reconstruction after training...")
    with torch.no_grad():
        test_data = data[:5]
        reconstructions = network.reconstruct(test_data)
        final_free_energy = network.compute_free_energy(test_data)
        
        print(f"Final free energy: {final_free_energy.item():.4f}")
        print(f"Reconstruction error: {torch.mean((test_data - reconstructions)**2).item():.4f}")
    
    # Visualize results (commented out for non-interactive environments)
    # print("\nVisualizing results...")
    # visualize_learning(free_energies)
    # visualize_reconstruction(test_data, reconstructions)
    
    print("\nDemo completed successfully!")
    print("The network learned to minimize prediction errors through hierarchical predictive coding.")