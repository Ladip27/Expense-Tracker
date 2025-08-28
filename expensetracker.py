import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import datetime
import json
import os
from collections import defaultdict
import pandas as pd

class Expense:
    def __init__(self, amount, category, date, description=""):
        self.amount = amount
        self.category = category
        self.date = date
        self.description = description
    
    def to_dict(self):
        return {
            "amount": self.amount,
            "category": self.category,
            "date": self.date.strftime("%Y-%m-%d"),
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data):
        date = datetime.datetime.strptime(data["date"], "%Y-%m-%d").date()
        return cls(data["amount"], data["category"], date, data.get("description", ""))

class ExpenseTracker:
    def __init__(self, filename="expenses.json"):
        self.expenses = []
        self.filename = filename
        self.categories = [
            "Food", "Transportation", "Entertainment", "Utilities", 
            "Rent/Mortgage", "Healthcare", "Education", "Shopping", "Other"
        ]
        self.load_expenses()
    
    def add_expense(self, amount, category, date, description=""):
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Expense amount must be positive")
            
            if category not in self.categories:
                raise ValueError("Invalid category")
                
            if isinstance(date, str):
                date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            
            expense = Expense(amount, category, date, description)
            self.expenses.append(expense)
            self.save_expenses()
            return True
            
        except ValueError as e:
            raise ValueError(f"Invalid input: {str(e)}")
        except Exception as e:
            raise Exception(f"Error adding expense: {str(e)}")
    
    def view_expenses(self, filter_category=None, filter_month=None, filter_year=None):
        filtered_expenses = self.expenses
        
        if filter_category and filter_category != "All":
            filtered_expenses = [e for e in filtered_expenses if e.category == filter_category]
        
        if filter_month:
            filtered_expenses = [e for e in filtered_expenses if e.date.month == filter_month]
        
        if filter_year:
            filtered_expenses = [e for e in filtered_expenses if e.date.year == filter_year]
            
        return filtered_expenses
    
    def monthly_summary(self, month=None, year=None):
        if not month:
            month = datetime.datetime.now().month
        if not year:
            year = datetime.datetime.now().year
            
        monthly_expenses = [e for e in self.expenses if e.date.month == month and e.date.year == year]
        
        total = sum(e.amount for e in monthly_expenses)
        by_category = defaultdict(float)
        
        for expense in monthly_expenses:
            by_category[expense.category] += expense.amount
            
        return {
            "total": total,
            "by_category": dict(by_category),
            "count": len(monthly_expenses)
        }
    
    def save_expenses(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump([e.to_dict() for e in self.expenses], f, indent=2)
        except Exception as e:
            raise Exception(f"Error saving expenses: {str(e)}")
    
    def load_expenses(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    self.expenses = [Expense.from_dict(item) for item in data]
            except Exception as e:
                raise Exception(f"Error loading expenses: {str(e)}")

class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.tracker = ExpenseTracker()
        
        self.setup_ui()
        self.refresh_expenses_list()
        self.update_summary()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Add expense section
        ttk.Label(main_frame, text="Add New Expense", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)
        
        ttk.Label(main_frame, text="Amount:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.amount_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.amount_var, width=15).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(main_frame, text="Category:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.category_var = tk.StringVar()
        category_combo = ttk.Combobox(main_frame, textvariable=self.category_var, values=self.tracker.categories, state="readonly", width=13)
        category_combo.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(main_frame, text="Date (YYYY-MM-DD):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        ttk.Entry(main_frame, textvariable=self.date_var, width=15).grid(row=3, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(main_frame, text="Description:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.desc_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.desc_var, width=15).grid(row=4, column=1, sticky=tk.W, pady=2)
        
        ttk.Button(main_frame, text="Add Expense", command=self.add_expense).grid(row=5, column=0, columnspan=2, pady=10)
        
        # Filters
        ttk.Label(main_frame, text="Filters", font=('Arial', 12, 'bold')).grid(row=0, column=2, columnspan=2, pady=(0, 10), sticky=tk.W)
        
        ttk.Label(main_frame, text="Category:").grid(row=1, column=2, sticky=tk.W, pady=2)
        self.filter_category_var = tk.StringVar(value="All")
        filter_category_combo = ttk.Combobox(main_frame, textvariable=self.filter_category_var, 
                                            values=["All"] + self.tracker.categories, state="readonly", width=13)
        filter_category_combo.grid(row=1, column=3, sticky=tk.W, pady=2)
        filter_category_combo.bind('<<ComboboxSelected>>', self.apply_filters)
        
        ttk.Label(main_frame, text="Month:").grid(row=2, column=2, sticky=tk.W, pady=2)
        self.filter_month_var = tk.StringVar(value="All")
        months = ["All"] + [datetime.date(2023, i, 1).strftime('%B') for i in range(1, 13)]
        filter_month_combo = ttk.Combobox(main_frame, textvariable=self.filter_month_var, values=months, state="readonly", width=13)
        filter_month_combo.grid(row=2, column=3, sticky=tk.W, pady=2)
        filter_month_combo.bind('<<ComboboxSelected>>', self.apply_filters)
        
        ttk.Label(main_frame, text="Year:").grid(row=3, column=2, sticky=tk.W, pady=2)
        current_year = datetime.datetime.now().year
        years = ["All"] + list(range(current_year-5, current_year+1))
        self.filter_year_var = tk.StringVar(value="All")
        filter_year_combo = ttk.Combobox(main_frame, textvariable=self.filter_year_var, 
                                        values=years, state="readonly", width=13)
        filter_year_combo.grid(row=3, column=3, sticky=tk.W, pady=2)
        filter_year_combo.bind('<<ComboboxSelected>>', self.apply_filters)
        
        ttk.Button(main_frame, text="Clear Filters", command=self.clear_filters).grid(row=4, column=2, columnspan=2, pady=10)
        
        # Expenses list
        ttk.Label(main_frame, text="Expenses", font=('Arial', 12, 'bold')).grid(row=6, column=0, columnspan=4, pady=(20, 5), sticky=tk.W)
        
        columns = ('date', 'category', 'amount', 'description')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=10)
        
        self.tree.heading('date', text='Date')
        self.tree.heading('category', text='Category')
        self.tree.heading('amount', text='Amount')
        self.tree.heading('description', text='Description')
        
        self.tree.column('date', width=100)
        self.tree.column('category', width=120)
        self.tree.column('amount', width=100)
        self.tree.column('description', width=200)
        
        self.tree.grid(row=7, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=7, column=4, sticky=(tk.N, tk.S))
        
        # Summary section
        summary_frame = ttk.LabelFrame(main_frame, text="Monthly Summary", padding="5")
        summary_frame.grid(row=8, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 5))
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, height=8, width=70)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights for resizing
        main_frame.rowconfigure(7, weight=1)
        for i in range(4):
            main_frame.columnconfigure(i, weight=1)
    
    def add_expense(self):
        try:
            amount = self.amount_var.get()
            category = self.category_var.get()
            date = self.date_var.get()
            description = self.desc_var.get()
            
            self.tracker.add_expense(amount, category, date, description)
            
            # Clear input fields
            self.amount_var.set("")
            self.desc_var.set("")
            
            self.refresh_expenses_list()
            self.update_summary()
            messagebox.showinfo("Success", "Expense added successfully!")
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def refresh_expenses_list(self):
        # Clear current treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get filter values
        category_filter = self.filter_category_var.get()
        if category_filter == "All":
            category_filter = None
            
        month_filter = None
        if self.filter_month_var.get() != "All":
            month_filter = list(datetime.datetime.strptime(self.filter_month_var.get(), "%B").month for _ in range(1))[0]
            
        year_filter = None
        if self.filter_year_var.get() != "All":
            year_filter = int(self.filter_year_var.get())
        
        # Get filtered expenses
        expenses = self.tracker.view_expenses(category_filter, month_filter, year_filter)
        
        # Add expenses to treeview
        for expense in expenses:
            self.tree.insert('', tk.END, values=(
                expense.date.strftime("%Y-%m-%d"),
                expense.category,
                f"${expense.amount:.2f}",
                expense.description
            ))
    
    def apply_filters(self, event=None):
        self.refresh_expenses_list()
    
    def clear_filters(self):
        self.filter_category_var.set("All")
        self.filter_month_var.set("All")
        self.filter_year_var.set("All")
        self.refresh_expenses_list()
    
    def update_summary(self):
        month = datetime.datetime.now().month
        year = datetime.datetime.now().year
        
        summary = self.tracker.monthly_summary(month, year)
        
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(tk.END, f"Summary for {datetime.date(1900, month, 1).strftime('%B')} {year}:\n\n")
        self.summary_text.insert(tk.END, f"Total Expenses: ${summary['total']:.2f}\n")
        self.summary_text.insert(tk.END, f"Number of Expenses: {summary['count']}\n\n")
        self.summary_text.insert(tk.END, "Breakdown by Category:\n")
        
        for category, amount in summary['by_category'].items():
            self.summary_text.insert(tk.END, f"  {category}: ${amount:.2f}\n")
        
        # Add pandas analysis
        df = pd.DataFrame([e.to_dict() for e in self.tracker.expenses])
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            current_month_expenses = df[(df['date'].dt.month == month) & (df['date'].dt.year == year)]
            
            if not current_month_expenses.empty:
                category_totals = current_month_expenses.groupby('category')['amount'].sum()
                largest_expense = current_month_expenses.loc[current_month_expenses['amount'].idxmax()]
                
                self.summary_text.insert(tk.END, f"\nLargest Expense: {largest_expense['category']} - ${largest_expense['amount']:.2f}\n")
                self.summary_text.insert(tk.END, f"Average Daily Spending: ${current_month_expenses['amount'].sum()/datetime.datetime.now().day:.2f}\n")

def main():
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()