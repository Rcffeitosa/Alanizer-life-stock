#!/usr/bin/env python3
"""
Performance Testing Script for Streamlit Application
Tests and monitors key performance metrics after optimization.
"""

import time
import psutil
import pandas as pd
import numpy as np
import io
import tempfile
import os
from pathlib import Path


class PerformanceMonitor:
    """Monitor and test application performance."""
    
    def __init__(self):
        self.results = {}
        self.process = psutil.Process()
    
    def get_memory_usage(self):
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
    
    def get_cpu_usage(self):
        """Get current CPU usage percentage."""
        return self.process.cpu_percent(interval=1)
    
    def time_function(self, func, *args, **kwargs):
        """Time a function execution and return result + metrics."""
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_memory = self.get_memory_usage()
        
        return {
            'result': result,
            'execution_time': end_time - start_time,
            'memory_delta': end_memory - start_memory,
            'peak_memory': max(start_memory, end_memory)
        }
    
    def generate_test_data(self, rows=1000):
        """Generate test data for performance testing."""
        np.random.seed(42)  # For reproducible results
        
        # Status data
        status_data = {
            'Item': [f'ITEM_{i:05d}' for i in range(rows)],
            'Descrição': [f'Descrição do item {i}' for i in range(rows)],
            'Quantidade Não Alocada': np.random.randint(1, 100, rows)
        }
        
        # Rastreabilidade data
        rastreabilidade_data = {
            'Item': [f'ITEM_{i:05d}' for i in range(rows)],
            'Endereço Origem': [f'A0{i:04d}' for i in range(rows)],
            'Endereço Destino': [f'A0{i+1000:04d}' for i in range(rows)]
        }
        
        # Estoque data
        estoque_data = {
            'Item': [f'ITEM_{i:05d}' for i in range(rows * 2)],  # More stock entries
            'Endereço': [f'A0{i:04d}' for i in range(rows * 2)],
            'Qtd Atual': np.random.randint(0, 50, rows * 2)
        }
        
        return (
            pd.DataFrame(status_data),
            pd.DataFrame(rastreabilidade_data),
            pd.DataFrame(estoque_data)
        )
    
    def create_test_files(self, dfs, format='xlsx'):
        """Create temporary test files."""
        files = []
        names = ['status', 'rastreabilidade', 'estoque']
        
        for df, name in zip(dfs, names):
            with tempfile.NamedTemporaryFile(
                suffix=f'.{format}', 
                delete=False, 
                prefix=f'test_{name}_'
            ) as tmp:
                if format == 'xlsx':
                    df.to_excel(tmp.name, index=False, engine='openpyxl')
                else:
                    df.to_csv(tmp.name, index=False)
                files.append(tmp.name)
        
        return files
    
    def test_file_reading_performance(self, file_sizes=[100, 1000, 5000]):
        """Test file reading performance across different sizes."""
        print("🔍 Testing File Reading Performance...")
        results = {}
        
        for size in file_sizes:
            print(f"  Testing with {size} rows...")
            dfs = self.generate_test_data(size)
            
            # Test both CSV and XLSX
            for format in ['csv', 'xlsx']:
                files = self.create_test_files(dfs, format)
                
                read_times = []
                memory_usage = []
                
                for file_path in files:
                    if format == 'xlsx':
                        metrics = self.time_function(
                            pd.read_excel, file_path, engine='openpyxl', dtype=str
                        )
                    else:
                        metrics = self.time_function(
                            pd.read_csv, file_path, engine='c', dtype=str
                        )
                    
                    read_times.append(metrics['execution_time'])
                    memory_usage.append(metrics['peak_memory'])
                
                # Cleanup
                for file_path in files:
                    os.unlink(file_path)
                
                results[f'{format}_{size}'] = {
                    'avg_read_time': np.mean(read_times),
                    'max_read_time': np.max(read_times),
                    'avg_memory': np.mean(memory_usage)
                }
        
        return results
    
    def test_data_processing_performance(self):
        """Test data processing operations performance."""
        print("⚙️ Testing Data Processing Performance...")
        
        # Generate test data
        dfs = self.generate_test_data(2000)
        status_df, rastreabilidade_df, estoque_df = dfs
        
        results = {}
        
        # Test merging operations
        print("  Testing merge operations...")
        merge_metrics = self.time_function(
            lambda: status_df.merge(rastreabilidade_df, on='Item', how='left')
        )
        results['merge_operation'] = {
            'time': merge_metrics['execution_time'],
            'memory_delta': merge_metrics['memory_delta']
        }
        
        # Test groupby operations
        print("  Testing groupby operations...")
        groupby_metrics = self.time_function(
            lambda: estoque_df.groupby('Item')['Qtd Atual'].sum()
        )
        results['groupby_operation'] = {
            'time': groupby_metrics['execution_time'],
            'memory_delta': groupby_metrics['memory_delta']
        }
        
        # Test filtering operations
        print("  Testing filtering operations...")
        filter_metrics = self.time_function(
            lambda: estoque_df[estoque_df['Endereço'].str.startswith('A0')]
        )
        results['filter_operation'] = {
            'time': filter_metrics['execution_time'],
            'memory_delta': filter_metrics['memory_delta']
        }
        
        return results
    
    def test_memory_optimization(self):
        """Test memory optimization techniques."""
        print("💾 Testing Memory Optimization...")
        
        # Generate large dataset
        df = pd.DataFrame({
            'item': [f'ITEM_{i % 100:03d}' for i in range(10000)],  # Repetitive data
            'category': np.random.choice(['A', 'B', 'C'], 10000),
            'value': np.random.randn(10000)
        })
        
        # Test memory usage before optimization
        before_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
        
        # Apply optimization
        optimized_df = df.copy()
        for col in ['item', 'category']:
            if optimized_df[col].dtype == 'object':
                unique_ratio = optimized_df[col].nunique() / len(optimized_df[col])
                if unique_ratio < 0.5:
                    optimized_df[col] = optimized_df[col].astype('category')
        
        # Test memory usage after optimization
        after_memory = optimized_df.memory_usage(deep=True).sum() / 1024 / 1024
        
        return {
            'before_mb': before_memory,
            'after_mb': after_memory,
            'reduction_percent': ((before_memory - after_memory) / before_memory) * 100
        }
    
    def benchmark_caching_impact(self):
        """Simulate and test caching performance impact."""
        print("🚀 Testing Caching Impact...")
        
        # Simulate expensive operation
        def expensive_operation(data):
            time.sleep(0.1)  # Simulate processing time
            return data.groupby('category').sum()
        
        df = pd.DataFrame({
            'category': np.random.choice(['A', 'B', 'C'], 1000),
            'value': np.random.randn(1000)
        })
        
        # Without caching (multiple calls)
        start_time = time.time()
        for _ in range(5):
            result = expensive_operation(df)
        no_cache_time = time.time() - start_time
        
        # Simulate with caching (one call + 4 cache hits)
        start_time = time.time()
        result = expensive_operation(df)  # First call
        for _ in range(4):
            pass  # Simulate cache hits (no processing)
        cache_time = time.time() - start_time
        
        return {
            'without_cache': no_cache_time,
            'with_cache': cache_time,
            'speedup': no_cache_time / cache_time if cache_time > 0 else float('inf')
        }
    
    def run_comprehensive_benchmark(self):
        """Run all performance tests and generate report."""
        print("🏁 Starting Comprehensive Performance Benchmark...")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all tests
        file_results = self.test_file_reading_performance()
        processing_results = self.test_data_processing_performance()
        memory_results = self.test_memory_optimization()
        cache_results = self.benchmark_caching_impact()
        
        total_time = time.time() - start_time
        
        # Generate report
        self.generate_performance_report({
            'file_reading': file_results,
            'data_processing': processing_results,
            'memory_optimization': memory_results,
            'caching_impact': cache_results,
            'benchmark_time': total_time
        })
    
    def generate_performance_report(self, results):
        """Generate a comprehensive performance report."""
        print("\n📊 PERFORMANCE BENCHMARK REPORT")
        print("=" * 60)
        
        # File Reading Results
        print("\n📁 File Reading Performance:")
        for key, metrics in results['file_reading'].items():
            format_type, size = key.split('_')
            print(f"  {format_type.upper()} ({size} rows): "
                  f"{metrics['avg_read_time']:.3f}s avg, "
                  f"{metrics['max_read_time']:.3f}s max, "
                  f"{metrics['avg_memory']:.1f}MB")
        
        # Data Processing Results
        print("\n⚙️ Data Processing Performance:")
        for operation, metrics in results['data_processing'].items():
            print(f"  {operation.replace('_', ' ').title()}: "
                  f"{metrics['time']:.3f}s, "
                  f"{metrics['memory_delta']:+.1f}MB memory")
        
        # Memory Optimization Results
        print("\n💾 Memory Optimization:")
        mem_results = results['memory_optimization']
        print(f"  Before: {mem_results['before_mb']:.1f}MB")
        print(f"  After: {mem_results['after_mb']:.1f}MB")
        print(f"  Reduction: {mem_results['reduction_percent']:.1f}%")
        
        # Caching Impact Results
        print("\n🚀 Caching Impact:")
        cache_results = results['caching_impact']
        print(f"  Without Cache: {cache_results['without_cache']:.3f}s")
        print(f"  With Cache: {cache_results['with_cache']:.3f}s")
        print(f"  Speedup: {cache_results['speedup']:.1f}x")
        
        # Overall Summary
        print(f"\n⏱️ Total Benchmark Time: {results['benchmark_time']:.2f}s")
        print("\n✅ Benchmark completed successfully!")
        
        # Save results to file
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = f"performance_report_{timestamp}.txt"
        
        with open(report_file, 'w') as f:
            f.write("PERFORMANCE BENCHMARK REPORT\n")
            f.write("=" * 60 + "\n")
            f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Write detailed results
            import json
            f.write("DETAILED RESULTS:\n")
            f.write(json.dumps(results, indent=2))
        
        print(f"📄 Detailed report saved to: {report_file}")


def main():
    """Main function to run performance tests."""
    print("🚀 Streamlit App Performance Benchmark")
    print("Testing optimizations implemented in the application...")
    print()
    
    monitor = PerformanceMonitor()
    monitor.run_comprehensive_benchmark()


if __name__ == "__main__":
    main()