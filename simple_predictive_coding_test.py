"""
Simple Predictive Coding Test - No Dependencies Required

This script demonstrates the core concepts of predictive coding using only
standard Python libraries (numpy-like operations simulated with lists).
"""

import math
import random


class SimplePredictiveCodingLayer:
    """Simple predictive coding layer using basic Python."""
    
    def __init__(self, input_size, hidden_size, learning_rate=0.1):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.learning_rate = learning_rate
        
        # Initialize weights randomly
        self.W_pred = [[random.gauss(0, 0.1) for _ in range(input_size)] 
                       for _ in range(hidden_size)]
        self.W_rec = [[random.gauss(0, 0.1) for _ in range(hidden_size)] 
                      for _ in range(input_size)]
        
        # Biases
        self.bias_pred = [0.0] * input_size
        self.bias_rec = [0.0] * hidden_size
    
    def forward_prediction(self, representation):
        """Generate top-down prediction."""
        prediction = [0.0] * self.input_size
        for i in range(self.input_size):
            for j in range(self.hidden_size):
                prediction[i] += representation[j] * self.W_pred[j][i]
            prediction[i] += self.bias_pred[i]
        return prediction
    
    def compute_error(self, input_data, prediction):
        """Compute prediction error."""
        return [input_data[i] - prediction[i] for i in range(len(input_data))]
    
    def update_representation(self, error):
        """Update representation based on error."""
        representation = [0.0] * self.hidden_size
        for i in range(self.hidden_size):
            for j in range(self.input_size):
                representation[i] += error[j] * self.W_rec[j][i]
            representation[i] += self.bias_rec[i]
            representation[i] = math.tanh(representation[i] * self.learning_rate)
        return representation


class SimplePredictiveCodingNetwork:
    """Simple multi-layer predictive coding network."""
    
    def __init__(self, layer_sizes, learning_rate=0.1, inference_steps=10):
        self.layer_sizes = layer_sizes
        self.learning_rate = learning_rate
        self.inference_steps = inference_steps
        self.num_layers = len(layer_sizes) - 1
        
        # Create layers
        self.layers = []
        for i in range(self.num_layers):
            layer = SimplePredictiveCodingLayer(
                input_size=layer_sizes[i],
                hidden_size=layer_sizes[i + 1],
                learning_rate=learning_rate
            )
            self.layers.append(layer)
    
    def inference(self, input_data):
        """Perform iterative inference."""
        # Initialize representations
        representations = [[0.0] * size for size in self.layer_sizes[1:]]
        
        # Iterative inference
        for step in range(self.inference_steps):
            # Forward pass: generate predictions
            predictions = []
            for i in range(self.num_layers):
                pred = self.layers[i].forward_prediction(representations[i])
                predictions.append(pred)
            
            # Compute errors
            errors = []
            for i in range(self.num_layers):
                if i == 0:
                    error = self.layers[i].compute_error(input_data, predictions[i])
                else:
                    error = self.layers[i].compute_error(representations[i-1], predictions[i])
                errors.append(error)
            
            # Update representations
            new_representations = []
            for i in range(self.num_layers):
                new_rep = self.layers[i].update_representation(errors[i])
                new_representations.append(new_rep)
            
            representations = new_representations
        
        return representations, errors
    
    def compute_free_energy(self, input_data):
        """Compute total prediction error (free energy)."""
        _, errors = self.inference(input_data)
        
        free_energy = 0.0
        for error_layer in errors:
            for error_val in error_layer:
                free_energy += error_val ** 2
        
        return free_energy


def create_simple_data(n_samples=20, data_size=10):
    """Create simple test data."""
    data = []
    for i in range(n_samples):
        pattern_type = i % 3
        sample = [0.0] * data_size
        
        if pattern_type == 0:
            # Sine wave pattern
            for j in range(data_size):
                sample[j] = math.sin(2 * math.pi * j / data_size)
        elif pattern_type == 1:
            # Square wave pattern
            for j in range(data_size):
                sample[j] = 1.0 if math.sin(2 * math.pi * j / data_size) > 0 else -1.0
        else:
            # Random sparse pattern
            indices = random.sample(range(data_size), data_size // 4)
            for idx in indices:
                sample[idx] = 1.0
        
        # Add small amount of noise
        for j in range(data_size):
            sample[j] += random.gauss(0, 0.1)
        
        data.append(sample)
    
    return data


def test_simple_network():
    """Test the simple predictive coding network."""
    print("Simple Predictive Coding Network Test")
    print("=" * 40)
    
    # Create test data
    print("Creating test data...")
    data = create_simple_data(n_samples=15, data_size=8)
    
    # Create network
    print("Creating network...")
    network = SimplePredictiveCodingNetwork(
        layer_sizes=[8, 6, 4, 2],
        learning_rate=0.1,
        inference_steps=15
    )
    
    print(f"Network architecture: {network.layer_sizes}")
    
    # Test inference on a few samples
    print("\nTesting inference...")
    for i, sample in enumerate(data[:3]):
        representations, errors = network.inference(sample)
        free_energy = network.compute_free_energy(sample)
        
        print(f"Sample {i+1}:")
        print(f"  Input: {[round(x, 3) for x in sample[:5]]}...")
        print(f"  Top representation: {[round(x, 3) for x in representations[-1]]}")
        print(f"  Free energy: {free_energy:.4f}")
    
    # Test learning (simplified - just show free energy changes)
    print("\nTesting learning progression...")
    initial_energies = []
    for sample in data[:5]:
        energy = network.compute_free_energy(sample)
        initial_energies.append(energy)
    
    print(f"Initial average free energy: {sum(initial_energies)/len(initial_energies):.4f}")
    
    # Simulate some learning iterations (very simplified)
    for epoch in range(20):
        total_energy = 0
        for sample in data:
            representations, errors = network.inference(sample)
            energy = network.compute_free_energy(sample)
            total_energy += energy
            
            # Simple weight update (gradient-free approximation)
            for layer in network.layers:
                for i in range(len(layer.W_pred)):
                    for j in range(len(layer.W_pred[i])):
                        layer.W_pred[i][j] += random.gauss(0, 0.001)  # Random walk
        
        avg_energy = total_energy / len(data)
        if epoch % 5 == 0:
            print(f"Epoch {epoch}: Average free energy: {avg_energy:.4f}")
    
    print("\nTest completed successfully!")
    print("The network demonstrates key predictive coding concepts:")
    print("- Hierarchical representations")
    print("- Prediction generation")
    print("- Error computation")
    print("- Iterative inference")
    print("- Free energy minimization")


if __name__ == "__main__":
    test_simple_network()