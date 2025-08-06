"""
Analytics Visualizer Module
Provides terminal-based data visualization and analytics capabilities
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.progress import Progress, BarColumn, TextColumn
from rich.layout import Layout
from rich.align import Align
from rich.rule import Rule
from datetime import datetime
from dataclasses import dataclass


@dataclass
class AnalyticsData:
    """Container for analytics data"""
    data: Union[pd.DataFrame, List[Dict], Dict]
    title: str
    chart_type: str = "table"
    x_column: Optional[str] = None
    y_column: Optional[str] = None


class TerminalAnalytics:
    """Terminal-based analytics and visualization system"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console(legacy_windows=False)
    
    def create_summary_stats(self, data: pd.DataFrame, title: str = "Summary Statistics") -> Panel:
        """Create summary statistics table"""
        if data.empty:
            return Panel("[red]No data available[/red]", title=title)
        
        # Create summary table
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="yellow", no_wrap=True)
        table.add_column("Value", justify="right")
        
        # Basic stats
        table.add_row("Total Records", f"{len(data):,}")
        table.add_row("Columns", f"{len(data.columns)}")
        table.add_row("Memory Usage", f"{data.memory_usage(deep=True).sum() / 1024:.1f} KB")
        
        # Numeric columns stats
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            table.add_row("[bold]Numeric Columns[/bold]", f"{len(numeric_cols)}")
            for col in numeric_cols[:5]:  # Show first 5 numeric columns
                values = data[col].dropna()
                if len(values) > 0:
                    table.add_row(f"  {col} (avg)", f"{values.mean():.2f}")
                    table.add_row(f"  {col} (min-max)", f"{values.min():.2f} - {values.max():.2f}")
        
        # String columns stats
        string_cols = data.select_dtypes(include=['object', 'string']).columns
        if len(string_cols) > 0:
            table.add_row("[bold]Text Columns[/bold]", f"{len(string_cols)}")
            for col in string_cols[:3]:  # Show first 3 string columns
                unique_count = data[col].nunique()
                table.add_row(f"  {col} (unique)", f"{unique_count}")
        
        return Panel(table, border_style="green")
    
    def create_bar_chart(self, data: Union[Dict, pd.Series], title: str = "Bar Chart", max_bars: int = 20) -> Panel:
        """Create a horizontal bar chart in terminal"""
        if isinstance(data, pd.Series):
            data = data.to_dict()
        
        if not data:
            return Panel("[red]No data for chart[/red]", title=title)
        
        # Sort and limit data
        sorted_data = dict(sorted(data.items(), key=lambda x: x[1], reverse=True)[:max_bars])
        
        # Calculate bar widths
        max_value = max(sorted_data.values()) if sorted_data.values() else 1
        max_label_width = max(len(str(k)) for k in sorted_data.keys()) if sorted_data else 10
        
        # Create the chart using ASCII characters for Windows compatibility
        chart_lines = []
        for label, value in sorted_data.items():
            bar_width = int((value / max_value) * 40) if max_value > 0 else 0
            bar = "#" * bar_width  # Use # instead of █ for Windows compatibility
            percentage = (value / max_value) * 100 if max_value > 0 else 0
            
            # Format the line
            label_str = f"{str(label)[:max_label_width]:<{max_label_width}}"
            value_str = f"{value:>8.0f}" if isinstance(value, (int, float)) else f"{value:>8}"
            
            chart_lines.append(f"{label_str} | {bar:<40} | {value_str} ({percentage:5.1f}%)")
        
        chart_text = "\n".join(chart_lines)
        return Panel(chart_text, title=title, border_style="blue")
    
    def create_data_table(self, data: pd.DataFrame, title: str = "Data Table", max_rows: int = 20) -> Panel:
        """Create a formatted data table"""
        if data.empty:
            return Panel("[red]No data available[/red]", title=title)
        
        # Limit rows and columns for display
        display_data = data.head(max_rows)
        
        # Create Rich table
        table = Table(title=f"{title} (showing {len(display_data)} of {len(data)} rows)", 
                     show_header=True, header_style="bold magenta")
        
        # Add columns
        for col in display_data.columns:
            table.add_column(str(col), overflow="ellipsis", max_width=20)
        
        # Add rows
        for _, row in display_data.iterrows():
            formatted_row = []
            for val in row:
                if pd.isna(val):
                    formatted_row.append("[dim]NULL[/dim]")
                elif isinstance(val, float):
                    formatted_row.append(f"{val:.2f}")
                elif isinstance(val, (int, np.integer)):
                    formatted_row.append(str(val))
                else:
                    formatted_row.append(str(val)[:50])  # Truncate long strings
            table.add_row(*formatted_row)
        
        return Panel(table, border_style="cyan")
    
    def create_distribution_chart(self, data: pd.Series, title: str = "Distribution", bins: int = 10) -> Panel:
        """Create a histogram-like distribution chart"""
        if data.empty:
            return Panel("[red]No data available[/red]", title=title)
        
        # Remove null values
        clean_data = data.dropna()
        
        if len(clean_data) == 0:
            return Panel("[red]No valid data after removing nulls[/red]", title=title)
        
        # Create histogram data
        if clean_data.dtype in ['object', 'string']:
            # For categorical data, show value counts
            hist_data = clean_data.value_counts().head(bins).to_dict()
        else:
            # For numeric data, create bins
            try:
                hist, bin_edges = np.histogram(clean_data, bins=bins)
                hist_data = {}
                for i in range(len(hist)):
                    bin_label = f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}"
                    hist_data[bin_label] = hist[i]
            except:
                # Fallback to value counts
                hist_data = clean_data.value_counts().head(bins).to_dict()
        
        return self.create_bar_chart(hist_data, f"{title} Distribution")
    
    def create_correlation_matrix(self, data: pd.DataFrame, title: str = "Correlation Matrix") -> Panel:
        """Create a correlation matrix visualization"""
        numeric_data = data.select_dtypes(include=[np.number])
        
        if numeric_data.empty or len(numeric_data.columns) < 2:
            return Panel("[yellow]Not enough numeric columns for correlation[/yellow]", title=title)
        
        # Calculate correlation
        corr = numeric_data.corr()
        
        # Create table
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("", style="yellow")
        
        for col in corr.columns:
            table.add_column(col[:10], justify="center", style="dim")
        
        for idx, row in corr.iterrows():
            row_data = [idx[:15]]
            for val in row:
                if pd.isna(val):
                    row_data.append("-")
                else:
                    # Color code correlation strength
                    if abs(val) > 0.7:
                        row_data.append(f"[bold red]{val:.2f}[/bold red]")
                    elif abs(val) > 0.3:
                        row_data.append(f"[yellow]{val:.2f}[/yellow]")
                    else:
                        row_data.append(f"[dim]{val:.2f}[/dim]")
            table.add_row(*row_data)
        
        return Panel(table, border_style="magenta")
    
    def create_analytics_dashboard(self, data: pd.DataFrame, title: str = "Analytics Dashboard") -> Layout:
        """Create a comprehensive analytics dashboard"""
        layout = Layout(name="root")
        
        # Top section - Summary
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1)
        )
        
        # Header
        header_text = Text(title, style="bold bright_blue", justify="center")
        timestamp = Text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                        style="dim", justify="center")
        layout["header"].update(Panel(Columns([header_text, timestamp]), border_style="blue"))
        
        # Body sections
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )
        
        # Left column - Summary stats and data preview
        layout["left"].split_column(
            Layout(name="stats", ratio=1),
            Layout(name="preview", ratio=1)
        )
        
        # Right column - Charts
        layout["right"].split_column(
            Layout(name="chart1", ratio=1),
            Layout(name="chart2", ratio=1)
        )
        
        # Populate sections
        layout["stats"].update(self.create_summary_stats(data, "Dataset Overview"))
        layout["preview"].update(self.create_data_table(data, "Data Preview", max_rows=10))
        
        # Add charts based on data
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            # First numeric column distribution
            layout["chart1"].update(self.create_distribution_chart(data[numeric_cols[0]], 
                                                                 f"{numeric_cols[0]} Distribution"))
            # Correlation matrix if multiple numeric columns
            if len(numeric_cols) > 1:
                layout["chart2"].update(self.create_correlation_matrix(data))
            else:
                # Show top values of first non-numeric column
                cat_cols = data.select_dtypes(include=['object', 'string']).columns
                if len(cat_cols) > 0:
                    top_values = data[cat_cols[0]].value_counts().head(10)
                    layout["chart2"].update(self.create_bar_chart(top_values, f"Top {cat_cols[0]} Values"))
        else:
            # Show value counts for categorical columns
            cat_cols = data.select_dtypes(include=['object', 'string']).columns
            if len(cat_cols) >= 2:
                layout["chart1"].update(self.create_bar_chart(
                    data[cat_cols[0]].value_counts().head(10), f"Top {cat_cols[0]} Values"))
                layout["chart2"].update(self.create_bar_chart(
                    data[cat_cols[1]].value_counts().head(10), f"Top {cat_cols[1]} Values"))
            elif len(cat_cols) == 1:
                layout["chart1"].update(self.create_bar_chart(
                    data[cat_cols[0]].value_counts().head(10), f"Top {cat_cols[0]} Values"))
                layout["chart2"].update(Panel("[yellow]Add more data for additional charts[/yellow]"))
        
        return layout
    
    def display_analytics(self, data: Union[pd.DataFrame, List[Dict], Dict], 
                         analytics_type: str = "dashboard", 
                         title: str = "Data Analytics"):
        """Main method to display analytics"""
        # Convert data to DataFrame if needed
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # If dict has uniform structure, try to convert
            try:
                df = pd.DataFrame([data])
            except:
                # Convert to simple key-value DataFrame
                df = pd.DataFrame(list(data.items()), columns=['Key', 'Value'])
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            self.console.print(Panel("[red]Unsupported data type for analytics[/red]", title="Error"))
            return
        
        if df.empty:
            self.console.print(Panel("[yellow]No data available for analytics[/yellow]", title=title))
            return
        
        # Display based on type
        if analytics_type == "dashboard":
            layout = self.create_analytics_dashboard(df, title)
            self.console.print(layout)
        elif analytics_type == "summary":
            panel = self.create_summary_stats(df, title)
            self.console.print(panel)
        elif analytics_type == "table":
            panel = self.create_data_table(df, title)
            self.console.print(panel)
        elif analytics_type == "correlation":
            panel = self.create_correlation_matrix(df, title)
            self.console.print(panel)
        else:
            # Default to dashboard
            layout = self.create_analytics_dashboard(df, title)
            self.console.print(layout)


def create_sample_analytics():
    """Create sample analytics for testing"""
    # Sample data
    sample_data = pd.DataFrame({
        'product': ['A', 'B', 'C', 'D', 'E', 'A', 'B', 'C'],
        'sales': [100, 150, 200, 80, 120, 90, 140, 180],
        'profit': [20, 30, 45, 15, 25, 18, 28, 38],
        'region': ['North', 'South', 'East', 'West', 'North', 'South', 'East', 'West'],
        'date': pd.date_range('2024-01-01', periods=8)
    })
    
    analytics = TerminalAnalytics()
    analytics.display_analytics(sample_data, analytics_type="dashboard", title="Sample Sales Analytics")


if __name__ == "__main__":
    create_sample_analytics()