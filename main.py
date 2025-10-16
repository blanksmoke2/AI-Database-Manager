import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
from datetime import datetime
import csv
import json
import os

class SQLiteManager(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("SQLite Database Manager Pro")
        self.geometry("1400x900")
        self.minsize(1000, 600)
        
        self.db_path = None
        self.conn = None
        self.cursor = None
        self.query_history = []
        self.current_table = None
        
        self.configure(bg="#1e1e1e")
        self.setup_styles()
        self.create_menu()
        self.create_widgets()
        self.create_statusbar()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        
        bg_dark = "#1e1e1e"
        bg_medium = "#2d2d2d"
        bg_light = "#3d3d3d"
        fg_color = "#ffffff"
        accent = "#0078d4"
        
        style.configure("TFrame", background=bg_dark)
        style.configure("TLabel", background=bg_dark, foreground=fg_color, font=("Segoe UI", 10))
        style.configure("TButton", background=bg_medium, foreground=fg_color, borderwidth=0, 
                       focuscolor='none', font=("Segoe UI", 9))
        style.map("TButton", background=[('active', accent)])
        
        style.configure("Accent.TButton", background=accent, foreground=fg_color, font=("Segoe UI", 9, "bold"))
        style.map("Accent.TButton", background=[('active', "#005a9e")])
        
        style.configure("Treeview", background=bg_medium, foreground=fg_color, 
                       fieldbackground=bg_medium, borderwidth=0, font=("Consolas", 9))
        style.configure("Treeview.Heading", background=bg_light, foreground=fg_color, 
                       borderwidth=1, font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[('selected', accent)])
        
        style.configure("TPanedwindow", background=bg_dark)
        
    def create_menu(self):
        menubar = tk.Menu(self, bg="#2d2d2d", fg="white", activebackground="#0078d4", 
						 activeforeground="white", tearoff=0)
        
        file_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white", 
						   activebackground="#0078d4", activeforeground="white")
        file_menu.add_command(label="New Database", command=self.new_database, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_database, accelerator="Ctrl+O")
        file_menu.add_command(label="Close", command=self.close_database)
        file_menu.add_separator()
        file_menu.add_command(label="Export", command=self.export_menu)
        file_menu.add_command(label="Import", command=self.import_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit, accelerator="Alt+F4")
        menubar.add_cascade(label="File", menu=file_menu)
        
      
        table_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white",
							activebackground="#0078d4", activeforeground="white")
        table_menu.add_command(label="New Table", command=self.create_table_dialog)
        table_menu.add_command(label="Drop Table", command=self.drop_table)
        table_menu.add_command(label="Truncate Table", command=self.truncate_table)
        table_menu.add_separator()
        table_menu.add_command(label="Table Info", command=self.show_table_info)
        menubar.add_cascade(label="Tables", menu=table_menu)
        
       
        query_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white",
							activebackground="#0078d4", activeforeground="white")
        query_menu.add_command(label="Execute Query", command=self.execute_query, accelerator="F5")
        query_menu.add_command(label="Query History", command=self.show_query_history)
        query_menu.add_command(label="Cancel", command=self.clear_query)
        menubar.add_cascade(label="Query", menu=query_menu)
        
        
        tools_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white",
							activebackground="#0078d4", activeforeground="white")
        tools_menu.add_command(label="VACUUM", command=self.vacuum_db)
        tools_menu.add_command(label="Integrity Check", command=self.integrity_check)
        tools_menu.add_command(label="Database Info", command=self.show_db_info)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
     
        help_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="white",
						   activebackground="#0078d4", activeforeground="white")
        help_menu.add_command(label="SQL Reference", command=self.show_sql_reference)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.config(menu=menubar)
        
       
        self.bind('<Control-n>', lambda e: self.new_database())
        self.bind('<Control-o>', lambda e: self.open_database())
        self.bind('<F5>', lambda e: self.execute_query())
        
    def create_widgets(self):
       
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        
        left_frame = ttk.Frame(main_paned, width=250)
        main_paned.add(left_frame, weight=0)
        
       
        db_info_frame = ttk.LabelFrame(left_frame, text="Database", padding=10)
        db_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.db_label = ttk.Label(db_info_frame, text="No database loaded", 
                                  wraplength=220, foreground="#888888")
        self.db_label.pack()
        
        btn_frame = ttk.Frame(db_info_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Open", command=self.open_database, 
                  style="Accent.TButton").pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(btn_frame, text="New", command=self.new_database).pack(side=tk.LEFT, expand=True, padx=2)
        
      
        table_frame = ttk.LabelFrame(left_frame, text="Tables", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
       
        search_frame = ttk.Frame(table_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.table_search = tk.Entry(search_frame, bg="#2d2d2d", fg="white", 
                                     insertbackground="white", relief=tk.FLAT, 
                                     font=("Segoe UI", 9))
        self.table_search.pack(fill=tk.X, ipady=3)
        self.table_search.insert(0, "Search...")
        self.table_search.bind('<FocusIn>', lambda e: self.clear_placeholder(e, "Search..."))
        self.table_search.bind('<FocusOut>', lambda e: self.set_placeholder(e, "Search..."))
        self.table_search.bind('<KeyRelease>', self.filter_tables)
        
     
        table_scroll = ttk.Scrollbar(table_frame)
        table_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.table_listbox = tk.Listbox(table_frame, yscrollcommand=table_scroll.set,
                                        bg="#2d2d2d", fg="white", selectbackground="#0078d4",
                                        selectforeground="white", relief=tk.FLAT,
                                        font=("Segoe UI", 10), activestyle='none')
        self.table_listbox.pack(fill=tk.BOTH, expand=True)
        table_scroll.config(command=self.table_listbox.yview)
        
        self.table_listbox.bind('<<ListboxSelect>>', self.on_table_select)
        self.table_listbox.bind('<Button-3>', self.show_table_context_menu)
        
    
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
      
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
    
        self.data_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.data_tab, text="📊 Data")
        self.create_data_tab()
        
      
        self.query_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.query_tab, text="⚡ SQL Query")
        self.create_query_tab()
        
    
        self.schema_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.schema_tab, text="🏗️ Schema")
        self.create_schema_tab()
        
    def create_data_tab(self):
        
        toolbar = ttk.Frame(self.data_tab)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="➕ Add Row", command=self.add_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ Edit", command=self.edit_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Delete", command=self.delete_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_data, 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(toolbar, text="📤 Export", command=self.export_table).pack(side=tk.LEFT, padx=2)
        
     
        filter_frame = ttk.Frame(toolbar)
        filter_frame.pack(side=tk.RIGHT)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        self.filter_entry = tk.Entry(filter_frame, width=20, bg="#2d2d2d", fg="white",
                                     insertbackground="white", relief=tk.FLAT)
        self.filter_entry.pack(side=tk.LEFT, ipady=3)
        self.filter_entry.bind('<Return>', lambda e: self.apply_filter())
        ttk.Button(filter_frame, text="Filter", command=self.apply_filter).pack(side=tk.LEFT, padx=2)
        
        
        tree_frame = ttk.Frame(self.data_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.data_tree = ttk.Treeview(tree_frame, yscrollcommand=vsb.set, 
                                      xscrollcommand=hsb.set, selectmode='browse')
        self.data_tree.pack(fill=tk.BOTH, expand=True)
        
        vsb.config(command=self.data_tree.yview)
        hsb.config(command=self.data_tree.xview)
        
        self.data_tree.bind('<Double-1>', lambda e: self.edit_row())
        
       
        self.row_count_label = ttk.Label(self.data_tab, text="No data")
        self.row_count_label.pack(pady=5)
        
    def create_query_tab(self):
        
        toolbar = ttk.Frame(self.query_tab)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="▶️ Execute (F5)", command=self.execute_query,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🧹 Clear", command=self.clear_query).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📜 History", command=self.show_query_history).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Save", command=self.save_query).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📂 Load", command=self.load_query).pack(side=tk.LEFT, padx=2)
        
       
        template_frame = ttk.Frame(toolbar)
        template_frame.pack(side=tk.RIGHT)
        
        ttk.Label(template_frame, text="Template:").pack(side=tk.LEFT, padx=5)
        self.template_combo = ttk.Combobox(template_frame, state='readonly', width=15)
        self.template_combo['values'] = ('SELECT *', 'INSERT INTO', 'UPDATE', 'DELETE FROM', 
                                         'CREATE TABLE', 'ALTER TABLE', 'DROP TABLE')
        self.template_combo.pack(side=tk.LEFT)
        self.template_combo.bind('<<ComboboxSelected>>', self.insert_template)
      
        editor_frame = ttk.Frame(self.query_tab)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
   
        self.line_numbers = tk.Text(editor_frame, width=4, bg="#252525", fg="#858585",
                                    relief=tk.FLAT, state='disabled', font=("Consolas", 10))
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        

        query_scroll = ttk.Scrollbar(editor_frame)
        query_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.query_text = tk.Text(editor_frame, wrap=tk.NONE, yscrollcommand=query_scroll.set,
                                  bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
                                  relief=tk.FLAT, font=("Consolas", 10), undo=True)
        self.query_text.pack(fill=tk.BOTH, expand=True)
        query_scroll.config(command=self.query_text.yview)
        
      
        self.query_text.tag_config("keyword", foreground="#569cd6")
        self.query_text.tag_config("string", foreground="#ce9178")
        self.query_text.tag_config("comment", foreground="#6a9955")
        self.query_text.tag_config("number", foreground="#b5cea8")
        
        self.query_text.bind('<KeyRelease>', self.update_line_numbers)
        self.query_text.bind('<KeyRelease>', self.syntax_highlight, add='+')
        
       
        result_frame = ttk.LabelFrame(self.query_tab, text="Result", padding=5)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
      
        result_tree_frame = ttk.Frame(result_frame)
        result_tree_frame.pack(fill=tk.BOTH, expand=True)
        
        result_vsb = ttk.Scrollbar(result_tree_frame, orient="vertical")
        result_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        result_hsb = ttk.Scrollbar(result_tree_frame, orient="horizontal")
        result_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.result_tree = ttk.Treeview(result_tree_frame, yscrollcommand=result_vsb.set,
                                        xscrollcommand=result_hsb.set)
        self.result_tree.pack(fill=tk.BOTH, expand=True)
        
        result_vsb.config(command=self.result_tree.yview)
        result_hsb.config(command=self.result_tree.xview)
        
        self.result_label = ttk.Label(result_frame, text="No query executed")
        self.result_label.pack(pady=5)
        
    def create_schema_tab(self):
        schema_frame = ttk.Frame(self.schema_tab)
        schema_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        schema_scroll = ttk.Scrollbar(schema_frame)
        schema_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.schema_tree = ttk.Treeview(schema_frame, yscrollcommand=schema_scroll.set)
        self.schema_tree.pack(fill=tk.BOTH, expand=True)
        schema_scroll.config(command=self.schema_tree.yview)
        
        self.schema_tree['columns'] = ('Type', 'Details')
        self.schema_tree.column('#0', width=200)
        self.schema_tree.column('Type', width=100)
        self.schema_tree.column('Details', width=400)
        
        self.schema_tree.heading('#0', text='Name')
        self.schema_tree.heading('Type', text='Type')
        self.schema_tree.heading('Details', text='Details')
        

        btn_frame = ttk.Frame(self.schema_tab)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="🔄 Refresh Schema", 
                  command=self.refresh_schema, style="Accent.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📋 Copy DDL", 
                  command=self.copy_ddl).pack(side=tk.LEFT, padx=2)
        
    def create_statusbar(self):
        self.statusbar = ttk.Label(self, text="Ready", relief=tk.FLAT, anchor=tk.W,
                                  background="#007acc", foreground="white",
                                  font=("Segoe UI", 9), padding=(10, 3))
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
   
    def new_database(self):
        file_path = filedialog.asksaveasfilename(
            title="Create New Database",
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                conn = sqlite3.connect(file_path)
                conn.close()
                self.open_database_file(file_path)
                self.set_status(f"New database created: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Database could not be created:\n{e}")
                
    def open_database(self):
        file_path = filedialog.askopenfilename(
            title="Open Database",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
        )
        if file_path:
            self.open_database_file(file_path)
            
    def open_database_file(self, file_path):
        try:
            if self.conn:
                self.conn.close()
                
            self.conn = sqlite3.connect(file_path)
            self.cursor = self.conn.cursor()
            self.db_path = file_path
            
            self.db_label.config(text=os.path.basename(file_path), foreground="white")
            self.refresh_tables()
            self.refresh_schema()
            self.set_status(f"Database opened: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Database could not be opened:\n{e}")
            
    def close_database(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            self.db_path = None
            self.db_label.config(text="No database loaded", foreground="#888888")
            self.table_listbox.delete(0, tk.END)
            self.clear_tree(self.data_tree)
            self.clear_tree(self.schema_tree)
            self.set_status("Database closed")
            
    def refresh_tables(self):
        if not self.conn:
            return
            
        self.table_listbox.delete(0, tk.END)
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = self.cursor.fetchall()
            for table in tables:
                self.table_listbox.insert(tk.END, table[0])
        except Exception as e:
            messagebox.showerror("Error", f"Tables could not be loaded:\n{e}")
            
    def filter_tables(self, event=None):
        if not self.conn:
            return
            
        search_term = self.table_search.get().lower()
        if search_term == "search..." or not search_term:
            self.refresh_tables()
            return
            
        self.table_listbox.delete(0, tk.END)
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = self.cursor.fetchall()
            for table in tables:
                if search_term in table[0].lower():
                    self.table_listbox.insert(tk.END, table[0])
        except Exception as e:
            pass
            
    def on_table_select(self, event=None):
        selection = self.table_listbox.curselection()
        if not selection:
            return
            
        self.current_table = self.table_listbox.get(selection[0])
        self.load_table_data(self.current_table)
        self.set_status(f"Table loaded: {self.current_table}")
        
    def load_table_data(self, table_name, where_clause=""):
        if not self.conn:
            return
            
        try:
            query = f"SELECT * FROM {table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
                
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            
          
            column_names = [description[0] for description in self.cursor.description]
            
           
            self.clear_tree(self.data_tree)
            self.data_tree['columns'] = column_names
            self.data_tree.column('#0', width=0, stretch=tk.NO)
            
            for col in column_names:
                self.data_tree.column(col, width=120, minwidth=80)
                self.data_tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
        
            for row in rows:
                self.data_tree.insert('', tk.END, values=row)
                
            self.row_count_label.config(text=f"Rows: {len(rows)} | Columns: {len(column_names)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Data could not be loaded:\n{e}")
            
    def sort_by_column(self, col):
        if not self.current_table:
            return
            
        try:
            self.cursor.execute(f"SELECT * FROM {self.current_table} ORDER BY {col}")
            rows = self.cursor.fetchall()
            
            self.clear_tree(self.data_tree)
            for row in rows:
                self.data_tree.insert('', tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Error", f"Sorting failed:\n{e}")
            
    def apply_filter(self):
        if not self.current_table:
            return
            
        filter_text = self.filter_entry.get()
        if not filter_text:
            self.load_table_data(self.current_table)
            return
            
        try:
        
            self.cursor.execute(f"PRAGMA table_info({self.current_table})")
            columns = [col[1] for col in self.cursor.fetchall()]
            
            where_parts = [f"{col} LIKE '%{filter_text}%'" for col in columns]
            where_clause = " OR ".join(where_parts)
            
            self.load_table_data(self.current_table, where_clause)
        except Exception as e:
            messagebox.showerror("Error", f"Filter could not be applied:\n{e}")
            
    def refresh_data(self):
        if self.current_table:
            self.load_table_data(self.current_table)
            
 
    def add_row(self):
        if not self.current_table:
            messagebox.showwarning("Warning", "Please select a table first.")
            return
            
        try:
            self.cursor.execute(f"PRAGMA table_info({self.current_table})")
            columns = self.cursor.fetchall()
            
            dialog = tk.Toplevel(self)
            dialog.title("Add New Row")
            dialog.geometry("500x400")
            dialog.configure(bg="#1e1e1e")
            dialog.transient(self)
            dialog.grab_set()
            
            canvas = tk.Canvas(dialog, bg="#1e1e1e", highlightthickness=0)
            scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            entries = {}
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = col[3]
                default = col[4]
                pk = col[5]
                
                frame = ttk.Frame(scrollable_frame)
                frame.pack(fill=tk.X, padx=10, pady=5)
                
                label_text = col_name
                if pk:
                    label_text += " (PK)"
                if not_null:
                    label_text += " *"
                    
                ttk.Label(frame, text=label_text, width=20).pack(side=tk.LEFT)
                
                if pk and 'INTEGER' in col_type.upper():
                    entry = tk.Entry(frame, bg="#2d2d2d", fg="white", insertbackground="white")
                    entry.insert(0, "AUTO")
                    entry.config(state='readonly')
                else:
                    entry = tk.Entry(frame, bg="#2d2d2d", fg="white", insertbackground="white")
                    if default:
                        entry.insert(0, default)
                        
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
                entries[col_name] = (entry, pk, col_type)
                
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            def save():
                try:
                    values = []
                    cols = []
                    for col_name, (entry, pk, col_type) in entries.items():
                        val = entry.get()
                        if val == "AUTO" and pk:
                            continue
                        cols.append(col_name)
                        values.append(val if val else None)
                        
                    placeholders = ','.join(['?' for _ in values])
                    col_str = ','.join(cols)
                    
                    self.cursor.execute(f"INSERT INTO {self.current_table} ({col_str}) VALUES ({placeholders})", values)
                    self.conn.commit()
                    self.refresh_data()
                    dialog.destroy()
                    self.set_status(f"Row added to {self.current_table}")
                except Exception as e:
                    messagebox.showerror("Error", f"Row could not be added:\n{e}")
                    
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(btn_frame, text="Save", command=save, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)
            
        except Exception as e:
            messagebox.showerror("Error", f"Dialog could not be created:\n{e}")
            
    def edit_row(self):
        if not self.current_table:
            messagebox.showwarning("Warning", "Please select a table first.")
            return
            
        selected = self.data_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a row to edit.")
            return
            
        try:
            item = self.data_tree.item(selected[0])
            values = item['values']
            
            self.cursor.execute(f"PRAGMA table_info({self.current_table})")
            columns = self.cursor.fetchall()
            
            dialog = tk.Toplevel(self)
            dialog.title("Edit Row")
            dialog.geometry("500x400")
            dialog.configure(bg="#1e1e1e")
            dialog.transient(self)
            dialog.grab_set()
            
            canvas = tk.Canvas(dialog, bg="#1e1e1e", highlightthickness=0)
            scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            entries = {}
            pk_info = []
            
            for i, col in enumerate(columns):
                col_name = col[1]
                pk = col[5]
                
                frame = ttk.Frame(scrollable_frame)
                frame.pack(fill=tk.X, padx=10, pady=5)
                
                label_text = col_name
                if pk:
                    label_text += " (PK)"
                    pk_info.append((col_name, values[i]))
                    
                ttk.Label(frame, text=label_text, width=20).pack(side=tk.LEFT)
                
                entry = tk.Entry(frame, bg="#2d2d2d", fg="white", insertbackground="white")
                if i < len(values):
                    entry.insert(0, str(values[i]))
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
                entries[col_name] = entry
                
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            def update():
                try:
                    set_parts = []
                    params = []
                    
                    for col_name, entry in entries.items():
                        set_parts.append(f"{col_name} = ?")
                        params.append(entry.get())
                        
                    where_parts = []
                    for pk_col, pk_val in pk_info:
                        where_parts.append(f"{pk_col} = ?")
                        params.append(pk_val)
                        
                    if not where_parts:
                        where_parts = [f"{col[1]} = ?" for col in columns]
                        params.extend(values)
                        
                    query = f"UPDATE {self.current_table} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"
                    self.cursor.execute(query, params)
                    self.conn.commit()
                    self.refresh_data()
                    dialog.destroy()
                    self.set_status(f"Row updated in {self.current_table}")
                except Exception as e:
                    messagebox.showerror("Error", f"Row could not be updated:\n{e}")
                    
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(btn_frame, text="Update", command=update, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)
            
        except Exception as e:
            messagebox.showerror("Error", f"Edit failed:\n{e}")
            
    def delete_row(self):
        if not self.current_table:
            messagebox.showwarning("Warning", "Please select a table first.")
            return
            
        selected = self.data_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a row to delete.")
            return
            
        if not messagebox.askyesno("Confirmation", "Do you really want to delete the selected row?"):
            return
            
        try:
            item = self.data_tree.item(selected[0])
            values = item['values']
            
            self.cursor.execute(f"PRAGMA table_info({self.current_table})")
            columns = self.cursor.fetchall()
            
    
            pk_cols = [col[1] for col in columns if col[5]]
            
            if pk_cols:
                where_parts = []
                params = []
                for pk_col in pk_cols:
                    idx = [col[1] for col in columns].index(pk_col)
                    where_parts.append(f"{pk_col} = ?")
                    params.append(values[idx])
                where_clause = " AND ".join(where_parts)
            else:
                where_parts = [f"{col[1]} = ?" for col in columns]
                where_clause = " AND ".join(where_parts)
                params = list(values)
                
            self.cursor.execute(f"DELETE FROM {self.current_table} WHERE {where_clause}", params)
            self.conn.commit()
            self.refresh_data()
            self.set_status(f"Row deleted from {self.current_table}")
        except Exception as e:
            messagebox.showerror("Error", f"Row could not be deleted:\n{e}")
            

    def create_table_dialog(self):
        if not self.conn:
            messagebox.showwarning("Warning", "Please open a database first.")
            return
            
        dialog = tk.Toplevel(self)
        dialog.title("Create New Table")
        dialog.geometry("700x500")
        dialog.configure(bg="#1e1e1e")
        dialog.transient(self)
        dialog.grab_set()
        
    
        name_frame = ttk.Frame(dialog)
        name_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(name_frame, text="Table name:").pack(side=tk.LEFT, padx=5)
        table_name_entry = tk.Entry(name_frame, bg="#2d2d2d", fg="white", insertbackground="white")
        table_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
    
        columns_frame = ttk.LabelFrame(dialog, text="Columns", padding=10)
        columns_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
      
        header = ttk.Frame(columns_frame)
        header.pack(fill=tk.X)
        
        ttk.Label(header, text="Name", width=20).grid(row=0, column=0, padx=5)
        ttk.Label(header, text="Typ", width=15).grid(row=0, column=1, padx=5)
        ttk.Label(header, text="PK", width=5).grid(row=0, column=2, padx=5)
        ttk.Label(header, text="NOT NULL", width=10).grid(row=0, column=3, padx=5)
        ttk.Label(header, text="UNIQUE", width=10).grid(row=0, column=4, padx=5)
        ttk.Label(header, text="Default", width=15).grid(row=0, column=5, padx=5)
        
   
        canvas = tk.Canvas(columns_frame, bg="#1e1e1e", highlightthickness=0, height=250)
        scrollbar = ttk.Scrollbar(columns_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        column_widgets = []
        
        def add_column_row():
            row = len(column_widgets)
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, pady=2)
            
            name_entry = tk.Entry(frame, width=20, bg="#2d2d2d", fg="white", insertbackground="white")
            name_entry.grid(row=0, column=0, padx=5)
            
            type_combo = ttk.Combobox(frame, width=15, state='readonly')
            type_combo['values'] = ('INTEGER', 'TEXT', 'REAL', 'BLOB', 'NUMERIC')
            type_combo.current(0)
            type_combo.grid(row=0, column=1, padx=5)
            
            pk_var = tk.BooleanVar()
            pk_check = ttk.Checkbutton(frame, variable=pk_var)
            pk_check.grid(row=0, column=2, padx=5)
            
            nn_var = tk.BooleanVar()
            nn_check = ttk.Checkbutton(frame, variable=nn_var)
            nn_check.grid(row=0, column=3, padx=5)
            
            uq_var = tk.BooleanVar()
            uq_check = ttk.Checkbutton(frame, variable=uq_var)
            uq_check.grid(row=0, column=4, padx=5)
            
            default_entry = tk.Entry(frame, width=15, bg="#2d2d2d", fg="white", insertbackground="white")
            default_entry.grid(row=0, column=5, padx=5)
            
            def remove():
                frame.destroy()
                column_widgets.remove(widgets)
                
            remove_btn = ttk.Button(frame, text="❌", width=3, command=remove)
            remove_btn.grid(row=0, column=6, padx=5)
            
            widgets = {
                'frame': frame,
                'name': name_entry,
                'type': type_combo,
                'pk': pk_var,
                'not_null': nn_var,
                'unique': uq_var,
                'default': default_entry
            }
            column_widgets.append(widgets)
            

        add_column_row()
        

        btn_frame = ttk.Frame(columns_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="➕ Add Column", command=add_column_row).pack(side=tk.LEFT, padx=5)
        

        sql_frame = ttk.LabelFrame(dialog, text="SQL Preview", padding=5)
        sql_frame.pack(fill=tk.X, padx=10, pady=5)
        
        sql_text = tk.Text(sql_frame, height=5, bg="#1e1e1e", fg="#d4d4d4", 
                          relief=tk.FLAT, font=("Consolas", 9))
        sql_text.pack(fill=tk.X)
        
        def update_preview():
            table_name = table_name_entry.get()
            if not table_name:
                sql_text.delete(1.0, tk.END)
                return
                
            cols = []
            for w in column_widgets:
                name = w['name'].get()
                if not name:
                    continue
                    
                col_def = f"{name} {w['type'].get()}"
                if w['pk'].get():
                    col_def += " PRIMARY KEY"
                if w['not_null'].get():
                    col_def += " NOT NULL"
                if w['unique'].get():
                    col_def += " UNIQUE"
                default = w['default'].get()
                if default:
                    col_def += f" DEFAULT {default}"
                cols.append(col_def)
                
            if cols:
                sql = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(cols) + "\n);"
                sql_text.delete(1.0, tk.END)
                sql_text.insert(1.0, sql)
                
        table_name_entry.bind('<KeyRelease>', lambda e: update_preview())
        
    
        action_frame = ttk.Frame(dialog)
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def create():
            update_preview()
            sql = sql_text.get(1.0, tk.END).strip()
            if not sql:
                messagebox.showwarning("Warning", "Please enter at least one column name.")
                return
                
            try:
                self.cursor.execute(sql)
                self.conn.commit()
                self.refresh_tables()
                self.refresh_schema()
                dialog.destroy()
                self.set_status(f"Table created: {table_name_entry.get()}")
            except Exception as e:
                messagebox.showerror("Error", f"Table could not be created:\n{e}")
                
        ttk.Button(action_frame, text="Create Table", command=create, 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT)
        
    def drop_table(self):
        selection = self.table_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a table.")
            return
            
        table_name = self.table_listbox.get(selection[0])
        
        if not messagebox.askyesno("Confirmation", f"Do you really want to permanently delete the table '{table_name}'?"):
            return
            
        try:
            self.cursor.execute(f"DROP TABLE {table_name}")
            self.conn.commit()
            self.refresh_tables()
            self.refresh_schema()
            self.clear_tree(self.data_tree)
            self.current_table = None
            self.set_status(f"Table dropped: {table_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Table could not be dropped:\n{e}")
            
    def truncate_table(self):
        selection = self.table_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a table.")
            return
            
        table_name = self.table_listbox.get(selection[0])
        
        if not messagebox.askyesno("Confirmation", f"Do you want to delete all data from the table '{table_name}'?"):
            return
            
        try:
            self.cursor.execute(f"DELETE FROM {table_name}")
            self.conn.commit()
            self.refresh_data()
            self.set_status(f"Table truncated: {table_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Table could not be truncated:\n{e}")
            
    def show_table_info(self):
        selection = self.table_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a table.")
            return
            
        table_name = self.table_listbox.get(selection[0])
        
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            info = self.cursor.fetchall()
            
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = self.cursor.fetchone()[0]
            
            dialog = tk.Toplevel(self)
            dialog.title(f"Table Info: {table_name}")
            dialog.geometry("700x400")
            dialog.configure(bg="#1e1e1e")
            dialog.transient(self)
            
   
            info_frame = ttk.Frame(dialog)
            info_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Label(info_frame, text=f"Table name: {table_name}", 
                     font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Row count: {row_count}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Column count: {len(info)}").pack(anchor=tk.W)
            

            tree_frame = ttk.Frame(dialog)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            tree = ttk.Treeview(tree_frame, columns=('Type', 'NOT NULL', 'Default', 'PK'), height=10)
            tree.pack(fill=tk.BOTH, expand=True)
            
            tree.column('#0', width=150)
            tree.column('Type', width=100)
            tree.column('NOT NULL', width=100)
            tree.column('Default', width=150)
            tree.column('PK', width=80)
            
            tree.heading('#0', text='Column name')
            tree.heading('Type', text='Data type')
            tree.heading('NOT NULL', text='NOT NULL')
            tree.heading('Default', text='Default')
            tree.heading('PK', text='Primary Key')
            
            for col in info:
                tree.insert('', tk.END, text=col[1], 
                          values=(col[2], 'Yes' if col[3] else 'No', 
                                 col[4] if col[4] else '', 'Yes' if col[5] else 'No'))
                                 
            ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Table info could not be loaded:\n{e}")
            

    def execute_query(self):
        if not self.conn:
            messagebox.showwarning("Warning", "Please open a database first.")
            return
            
        query = self.query_text.get(1.0, tk.END).strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter an SQL query.")
            return
            
        try:
            start_time = datetime.now()
            self.cursor.execute(query)
            
       
            if query.upper().strip().startswith('SELECT'):
                rows = self.cursor.fetchall()
                columns = [desc[0] for desc in self.cursor.description]
                
                self.clear_tree(self.result_tree)
                self.result_tree['columns'] = columns
                self.result_tree.column('#0', width=0, stretch=tk.NO)
                
                for col in columns:
                    self.result_tree.column(col, width=120)
                    self.result_tree.heading(col, text=col)
                    
                for row in rows:
                    self.result_tree.insert('', tk.END, values=row)
                    
                exec_time = (datetime.now() - start_time).total_seconds()
                self.result_label.config(text=f"Rows: {len(rows)} | Time: {exec_time:.3f}s")
                
            else:
                self.conn.commit()
                exec_time = (datetime.now() - start_time).total_seconds()
                affected = self.cursor.rowcount
                self.result_label.config(text=f"Query successful | Affected rows: {affected} | Time: {exec_time:.3f}s")
                self.clear_tree(self.result_tree)
                self.refresh_tables()
                self.refresh_schema()
                if self.current_table:
                    self.refresh_data()
                    
   
            self.query_history.append({
                'query': query,
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'success': True
            })
            
            self.set_status("Query executed successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Query failed:\n{e}")
            self.query_history.append({
                'query': query,
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'success': False,
                'error': str(e)
            })
            
    def clear_query(self):
        self.query_text.delete(1.0, tk.END)
        
    def show_query_history(self):
        if not self.query_history:
            messagebox.showinfo("Info", "No query history available.")
            return
            
        dialog = tk.Toplevel(self)
        dialog.title("Query History")
        dialog.geometry("800x500")
        dialog.configure(bg="#1e1e1e")
        dialog.transient(self)
        
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tree = ttk.Treeview(tree_frame, columns=('Zeit', 'Status'), height=15)
        tree.pack(fill=tk.BOTH, expand=True)
        
        tree.column('#0', width=500)
        tree.column('Zeit', width=150)
        tree.column('Status', width=100)
        
        tree.heading('#0', text='Query')
        tree.heading('Zeit', text='Time')
        tree.heading('Status', text='Status')
        
        for entry in reversed(self.query_history[-50:]):  # Letzte 50
            status = '✓ Success' if entry['success'] else '✗ Error'
            query_preview = entry['query'][:60] + '...' if len(entry['query']) > 60 else entry['query']
            tree.insert('', 0, text=query_preview, values=(entry['time'], status))
            
        def use_query(event):
            selection = tree.selection()
            if selection:
                idx = len(self.query_history) - 1 - tree.index(selection[0])
                self.query_text.delete(1.0, tk.END)
                self.query_text.insert(1.0, self.query_history[idx]['query'])
                dialog.destroy()
                self.notebook.select(self.query_tab)
                
        tree.bind('<Double-1>', use_query)
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
        
    def save_query(self):
        query = self.query_text.get(1.0, tk.END).strip()
        if not query:
            messagebox.showwarning("Warning", "No query to save.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save Query",
            defaultextension=".sql",
            filetypes=[("SQL Files", "*.sql"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(query)
                self.set_status(f"Query saved: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Query could not be saved:\n{e}")
                
    def load_query(self):
        file_path = filedialog.askopenfilename(
            title="Load Query",
            filetypes=[("SQL Files", "*.sql"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    query = f.read()
                self.query_text.delete(1.0, tk.END)
                self.query_text.insert(1.0, query)
                self.set_status(f"Query loaded: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Query could not be loaded:\n{e}")
                
    def insert_template(self, event=None):
        template = self.template_combo.get()
        if not template:
            return
            
        templates = {
            'SELECT *': 'SELECT * FROM table_name WHERE condition;',
            'INSERT INTO': 'INSERT INTO table_name (column1, column2) VALUES (value1, value2);',
            'UPDATE': 'UPDATE table_name SET column1 = value1 WHERE condition;',
            'DELETE FROM': 'DELETE FROM table_name WHERE condition;',
            'CREATE TABLE': 'CREATE TABLE table_name (\n  id INTEGER PRIMARY KEY,\n  column1 TEXT NOT NULL\n);',
            'ALTER TABLE': 'ALTER TABLE table_name ADD COLUMN column_name TEXT;',
            'DROP TABLE': 'DROP TABLE IF EXISTS table_name;'
        }
        
        self.query_text.insert(tk.INSERT, templates.get(template, template))
        
    def syntax_highlight(self, event=None):
        keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 
                   'DELETE', 'CREATE', 'TABLE', 'ALTER', 'DROP', 'AND', 'OR', 'NOT', 'NULL',
                   'PRIMARY', 'KEY', 'FOREIGN', 'UNIQUE', 'INDEX', 'JOIN', 'LEFT', 'RIGHT',
                   'INNER', 'OUTER', 'ON', 'AS', 'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT']
        
        content = self.query_text.get(1.0, tk.END)
        
        self.query_text.tag_remove("keyword", 1.0, tk.END)
        
        for word in keywords:
            start = 1.0
            while True:
                pos = self.query_text.search(r'\m' + word + r'\M', start, tk.END, regexp=True, nocase=True)
                if not pos:
                    break
                end = f"{pos}+{len(word)}c"
                self.query_text.tag_add("keyword", pos, end)
                start = end
                
    def update_line_numbers(self, event=None):
        lines = self.query_text.get(1.0, tk.END).count('\n')
        line_numbers_string = "\n".join(str(i) for i in range(1, lines + 1))
        
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)
        self.line_numbers.insert(1.0, line_numbers_string)
        self.line_numbers.config(state='disabled')
        
    def refresh_schema(self):
        if not self.conn:
            return
            
        self.clear_tree(self.schema_tree)
        
        try:

            self.cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = self.cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                table_sql = table[1]
                
                table_node = self.schema_tree.insert('', tk.END, text=table_name, 
                                                     values=('Table', ''), tags=('table',))
                

                self.cursor.execute(f"PRAGMA table_info({table_name})")
                columns = self.cursor.fetchall()
                
                for col in columns:
                    col_name = col[1]
                    col_type = col[2]
                    not_null = col[3]
                    default = col[4]
                    pk = col[5]
                    
                    details = []
                    if pk:
                        details.append("PRIMARY KEY")
                    if not_null:
                        details.append("NOT NULL")
                    if default:
                        details.append(f"DEFAULT {default}")
                        
                    self.schema_tree.insert(table_node, tk.END, text=col_name,
                                          values=(col_type, ', '.join(details)))
                                          
   
            self.cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' ORDER BY name")
            indexes = self.cursor.fetchall()
            
            if indexes:
                index_root = self.schema_tree.insert('', tk.END, text='📑 Indexes', 
                                                     values=('', ''), tags=('category',))
                for idx in indexes:
                    if idx[0] and not idx[0].startswith('sqlite_'):
                        self.schema_tree.insert(index_root, tk.END, text=idx[0],
                                              values=('Index', idx[1] if idx[1] else ''))
                                          
  
            self.cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='view' ORDER BY name")
            views = self.cursor.fetchall()
            
            if views:
                view_root = self.schema_tree.insert('', tk.END, text='👁️ Views', 
                                                    values=('', ''), tags=('category',))
                for view in views:
                    self.schema_tree.insert(view_root, tk.END, text=view[0],
                                          values=('View', view[1] if view[1] else ''))
                                          
    
            self.cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger' ORDER BY name")
            triggers = self.cursor.fetchall()
            
            if triggers:
                trigger_root = self.schema_tree.insert('', tk.END, text='⚡ Triggers',
                                                      values=('', ''), tags=('category',))
                for trigger in triggers:
                    self.schema_tree.insert(trigger_root, tk.END, text=trigger[0],
                                          values=('Trigger', trigger[1] if trigger[1] else ''))
                                          
        except Exception as e:
            messagebox.showerror("Error", f"Schema could not be loaded:\n{e}")
            
    def copy_ddl(self):
        selection = self.schema_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item.")
            return
            
        item = self.schema_tree.item(selection[0])
        item_text = item['text']
        
        try:
            self.cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{item_text}'")
            result = self.cursor.fetchone()
            
            if result and result[0]:
                self.clipboard_clear()
                self.clipboard_append(result[0])
                self.set_status(f"DDL copied to clipboard: {item_text}")
            else:
                messagebox.showinfo("Info", "No DDL available for this item.")
                
        except Exception as e:
            messagebox.showerror("Error", f"DDL could not be copied:\n{e}")
            

    def export_menu(self):
        if not self.conn:
            messagebox.showwarning("Warning", "Please open a database first.")
            return
            
        dialog = tk.Toplevel(self)
        dialog.title("Export Database")
        dialog.geometry("400x250")
        dialog.configure(bg="#1e1e1e")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Choose export format:", 
                 font=("Segoe UI", 11, "bold")).pack(pady=20)
        
        ttk.Button(dialog, text="📄 SQL Dump", command=lambda: [self.export_sql(), dialog.destroy()],
                  style="Accent.TButton").pack(fill=tk.X, padx=50, pady=5)
        ttk.Button(dialog, text="📊 CSV Export (all tables)", 
                  command=lambda: [self.export_all_csv(), dialog.destroy()]).pack(fill=tk.X, padx=50, pady=5)
        ttk.Button(dialog, text="📋 JSON Export", 
                  command=lambda: [self.export_json(), dialog.destroy()]).pack(fill=tk.X, padx=50, pady=5)
        
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=10)
        
    def export_sql(self):
        file_path = filedialog.asksaveasfilename(
            title="Save SQL Dump",
            defaultextension=".sql",
            filetypes=[("SQL Files", "*.sql"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for line in self.conn.iterdump():
                        f.write(f'{line}\n')
                        
                messagebox.showinfo("Success", f"Database successfully exported to:\n{file_path}")
                self.set_status("SQL dump exported successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed:\n{e}")
                
    def export_all_csv(self):
        folder = filedialog.askdirectory(title="Choose folder for CSV export")
        
        if folder:
            try:
                self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = self.cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    file_path = os.path.join(folder, f"{table_name}.csv")
                    
                    self.cursor.execute(f"SELECT * FROM {table_name}")
                    rows = self.cursor.fetchall()
                    columns = [desc[0] for desc in self.cursor.description]
                    
                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(columns)
                        writer.writerows(rows)
                        
                messagebox.showinfo("Success", f"{len(tables)} tables successfully exported to CSV.")
                self.set_status(f"{len(tables)} CSV files exported")
            except Exception as e:
                messagebox.showerror("Error", f"CSV export failed:\n{e}")
                
    def export_table(self):
        if not self.current_table:
            messagebox.showwarning("Warning", "Please select a table first.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title=f"Export table '{self.current_table}'",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                self.cursor.execute(f"SELECT * FROM {self.current_table}")
                rows = self.cursor.fetchall()
                columns = [desc[0] for desc in self.cursor.description]
                
                if file_path.endswith('.json'):
                    data = [dict(zip(columns, row)) for row in rows]
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(columns)
                        writer.writerows(rows)
                        
                messagebox.showinfo("Success", f"Table exported successfully:\n{file_path}")
                self.set_status(f"Table {self.current_table} exported")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed:\n{e}")
                
    def export_json(self):
        file_path = filedialog.asksaveasfilename(
            title="Export database as JSON",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = self.cursor.fetchall()
                
                db_data = {}
                for table in tables:
                    table_name = table[0]
                    self.cursor.execute(f"SELECT * FROM {table_name}")
                    rows = self.cursor.fetchall()
                    columns = [desc[0] for desc in self.cursor.description]
                    
                    db_data[table_name] = [dict(zip(columns, row)) for row in rows]
                    
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(db_data, f, indent=2, ensure_ascii=False)
                    
                messagebox.showinfo("Success", f"Database exported to JSON successfully.")
                self.set_status("JSON export successful")
            except Exception as e:
                messagebox.showerror("Error", f"JSON export failed:\n{e}")
                
    def import_menu(self):
        if not self.conn:
            messagebox.showwarning("Warning", "Please open a database first.")
            return
            
        dialog = tk.Toplevel(self)
        dialog.title("Import Data")
        dialog.geometry("400x200")
        dialog.configure(bg="#1e1e1e")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Choose import format:",
                 font=("Segoe UI", 11, "bold")).pack(pady=20)
        
        ttk.Button(dialog, text="📄 SQL File", command=lambda: [self.import_sql(), dialog.destroy()],
                  style="Accent.TButton").pack(fill=tk.X, padx=50, pady=5)
        ttk.Button(dialog, text="📊 CSV File",
                  command=lambda: [self.import_csv(), dialog.destroy()]).pack(fill=tk.X, padx=50, pady=5)
        
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(pady=10)
        
    def import_sql(self):
        file_path = filedialog.askopenfilename(
            title="Import SQL File",
            filetypes=[("SQL Files", "*.sql"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                    
                self.cursor.executescript(sql_script)
                self.conn.commit()
                
                self.refresh_tables()
                self.refresh_schema()
                
                messagebox.showinfo("Success", "SQL file imported successfully.")
                self.set_status("SQL import successful")
            except Exception as e:
                messagebox.showerror("Error", f"Import failed:\n{e}")
                
    def import_csv(self):
        file_path = filedialog.askopenfilename(
            title="Import CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
            
        table_name = simpledialog.askstring("Table name", 
                                           "Name for the new table:",
                                           initialvalue=os.path.splitext(os.path.basename(file_path))[0])
        
        if not table_name:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                first_row = next(reader)
                
                
                col_defs = []
                for i, header in enumerate(headers):
                    col_name = header.strip().replace(' ', '_')
                    try:
                        float(first_row[i])
                        col_type = "REAL" if '.' in first_row[i] else "INTEGER"
                    except:
                        col_type = "TEXT"
                    col_defs.append(f"{col_name} {col_type}")
                
                
                create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(col_defs)})"
                self.cursor.execute(create_sql)
                
               
                f.seek(0)
                reader = csv.reader(f)
                next(reader) 
                
                placeholders = ','.join(['?' for _ in headers])
                insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
                
                rows_imported = 0
                for row in reader:
                    self.cursor.execute(insert_sql, row)
                    rows_imported += 1
                    
                self.conn.commit()
                self.refresh_tables()
                self.refresh_schema()
                
                messagebox.showinfo("Success", f"{rows_imported} rows successfully imported into table '{table_name}'.")
                self.set_status(f"CSV import successful: {rows_imported} rows")
                
        except Exception as e:
            messagebox.showerror("Error", f"CSV import failed:\n{e}")
            
  
    def vacuum_db(self):
        if not self.conn:
            messagebox.showwarning("Warning", "Please open a database first.")
            return
            
        if messagebox.askyesno("VACUUM", 
            "This will optimize the database and release unused space.\nContinue?"):
            try:
                self.cursor.execute("VACUUM")
                self.conn.commit()
                messagebox.showinfo("Success", "Database optimized successfully.")
                self.set_status("VACUUM completed successfully")
            except Exception as e:
                messagebox.showerror("Error", f"VACUUM failed:\n{e}")
                
    def integrity_check(self):
        if not self.conn:
            messagebox.showwarning("Warning", "Please open a database first.")
            return
            
        try:
            self.cursor.execute("PRAGMA integrity_check")
            result = self.cursor.fetchall()
            
            if result[0][0] == 'ok':
                messagebox.showinfo("Integrity", "✓ Database is OK.")
            else:
                messagebox.showwarning("Integrity", f"Problems found:\n{result}")
                
            self.set_status("Integrity check completed")
        except Exception as e:
            messagebox.showerror("Error", f"Integrity check failed:\n{e}")
            
    def show_db_info(self):
        if not self.conn:
            messagebox.showwarning("Warning", "Please open a database first.")
            return
            
        try:
            
            self.cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
            index_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='view'")
            view_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'")
            trigger_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("PRAGMA page_count")
            page_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("PRAGMA page_size")
            page_size = self.cursor.fetchone()[0]
            
            db_size = page_count * page_size / (1024 * 1024)  # MB
            
            self.cursor.execute("PRAGMA encoding")
            encoding = self.cursor.fetchone()[0]
            
            
            dialog = tk.Toplevel(self)
            dialog.title("Database Information")
            dialog.geometry("500x400")
            dialog.configure(bg="#1e1e1e")
            dialog.transient(self)
            
            info_frame = ttk.Frame(dialog)
            info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            ttk.Label(info_frame, text="Database Information",
                     font=("Segoe UI", 14, "bold")).pack(pady=(0, 20))
            
            info = [
                ("File", os.path.basename(self.db_path)),
                ("Path", self.db_path),
                ("Size", f"{db_size:.2f} MB"),
                ("Encoding", encoding),
                ("", ""),
                ("Tables", str(table_count)),
                ("Indexes", str(index_count)),
                ("Views", str(view_count)),
                ("Triggers", str(trigger_count)),
                ("", ""),
                ("Page Size", f"{page_size} Bytes"),
                ("Page Count", str(page_count)),
            ]
            
            for label, value in info:
                if not label:
                    ttk.Separator(info_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
                else:
                    frame = ttk.Frame(info_frame)
                    frame.pack(fill=tk.X, pady=3)
                    ttk.Label(frame, text=f"{label}:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
                    ttk.Label(frame, text=value).pack(side=tk.RIGHT)
                    
            ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Information could not be loaded:\n{e}")
            
    
    def show_table_context_menu(self, event):
        selection = self.table_listbox.curselection()
        if not selection:
            return
        
        menu = tk.Menu(self, tearoff=0, bg="#2d2d2d", fg="white",
                      activebackground="#0078d4", activeforeground="white")
        
        menu.add_command(label="Show Data", command=lambda: self.on_table_select())
        menu.add_command(label="Table Info", command=self.show_table_info)
        menu.add_separator()
        menu.add_command(label="Export", command=self.export_table)
        menu.add_separator()
        menu.add_command(label="Truncate Table", command=self.truncate_table)
        menu.add_command(label="Drop Table", command=self.drop_table)
        
        menu.post(event.x_root, event.y_root)
        
    
    def show_sql_reference(self):
        dialog = tk.Toplevel(self)
        dialog.title("SQL Reference")
        dialog.geometry("700x600")
        dialog.configure(bg="#1e1e1e")
        dialog.transient(self)
        
        text = tk.Text(dialog, bg="#1e1e1e", fg="#d4d4d4", wrap=tk.WORD,
                      font=("Consolas", 10), padx=20, pady=20)
        text.pack(fill=tk.BOTH, expand=True)
        
        sql_ref = """
SQLite SQL Reference - Quick Guide

DATA QUERYING
------------
SELECT * FROM table;
SELECT column1, column2 FROM table WHERE condition;
SELECT * FROM table ORDER BY column ASC/DESC;
SELECT * FROM table LIMIT 10 OFFSET 5;
SELECT COUNT(*), AVG(column) FROM table GROUP BY column;

INSERTING DATA
--------------
INSERT INTO table (column1, column2) VALUES (value1, value2);
INSERT INTO table VALUES (value1, value2, value3);

UPDATING DATA
-------------
UPDATE table SET column1 = value1 WHERE condition;

DELETING DATA
-------------
DELETE FROM table WHERE condition;
DELETE FROM table; -- Delete all rows

CREATING TABLES
---------------
CREATE TABLE table (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  age INTEGER,
  email TEXT UNIQUE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

ALTERING TABLES
---------------
ALTER TABLE table ADD COLUMN new_column TEXT;
ALTER TABLE table RENAME TO new_name;
DROP TABLE table;

JOINS
-----
SELECT * FROM tab1 INNER JOIN tab2 ON tab1.id = tab2.fk_id;
SELECT * FROM tab1 LEFT JOIN tab2 ON tab1.id = tab2.fk_id;

AGGREGATE FUNCTIONS
-------------------
COUNT(), SUM(), AVG(), MIN(), MAX()

OPERATORS
---------
=, !=, <, >, <=, >=
LIKE, IN, BETWEEN, IS NULL, IS NOT NULL
AND, OR, NOT

WILDCARDS
---------
%  - any sequence of characters
_  - a single character

Example: SELECT * FROM users WHERE name LIKE 'A%';
"""
        
        text.insert(1.0, sql_ref)
        text.config(state='disabled')
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
        
    def show_about(self):
        messagebox.showinfo("About SQLite Manager Pro",
            "SQLite Database Manager Pro\n\n"
            "Version 1.0\n\n"
            "A full-featured SQLite database manager\n"
            "with essential capabilities:\n\n"
            "• View, edit, and delete data\n"
            "• SQL queries with syntax highlighting\n"
            "• Schema visualization\n"
            "• Import/Export (SQL, CSV, JSON)\n"
            "• Manage tables\n"
            "• Query history\n"
            "• And much more!\n\n"
            "Built with Python and Tkinter")
        
   
    def clear_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)
            
    def set_status(self, message):
        self.statusbar.config(text=message)
        self.after(5000, lambda: self.statusbar.config(text="Ready"))
        
    def clear_placeholder(self, event, placeholder):
        if event.widget.get() == placeholder:
            event.widget.delete(0, tk.END)
            event.widget.config(fg="white")
            
    def set_placeholder(self, event, placeholder):
        if not event.widget.get():
            event.widget.insert(0, placeholder)
            event.widget.config(fg="#888888")

if __name__ == "__main__":
    app = SQLiteManager()
    app.mainloop()