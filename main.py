import tkinter as tk
import tkinter.messagebox as msg
import os
import sqlite3
from tkinter.colorchooser import *

class Todo(tk.Tk):
    def __init__(self, tasks=None):
        super().__init__()

        if not tasks:
            self.tasks = []
        else:
            self.tasks = tasks


        self.tasks_canvas = tk.Canvas(self)

        self.FRAME_tasks = tk.Frame(self.tasks_canvas)
        self.FRAME_window = tk.Frame(self)


        self.scrollbar = tk.Scrollbar(self.tasks_canvas, orient="vertical", command=self.tasks_canvas.yview)
        self.tasks_canvas.configure(yscrollcommand=self.scrollbar.set)


        self.title("To-Do App")
        self.geometry("400x600")



        self.task_create = tk.Text(self.FRAME_window, height=3, bg="white", fg="black")

        self.add_category_button = tk.Button(self.FRAME_window,text="Add category",command=self.new_category_window)

        self.display_by_category_button = tk.Button(self.FRAME_window,text="Display by category",command=self.display_by_categories_window)

        self.tasks_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)


        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas_frame = self.tasks_canvas.create_window((0, 0), window=self.FRAME_tasks, anchor="n")

        self.task_create.pack(side=tk.BOTTOM, fill=tk.X)
        self.FRAME_window.pack(side=tk.BOTTOM, fill=tk.X)
        self.task_create.focus_set()
        self.add_category_button.pack(side=tk.BOTTOM)
        self.display_by_category_button.pack(side=tk.BOTTOM)
        self.colour_schemes = [{"bg": "lightgrey", "fg": "black"}, {"bg": "grey", "fg": "white"}]

        #load from the db
        current_tasks = self.load_tasks()
        for task in current_tasks:
            task_text = task[0]
            task_category=task[1]
            task_dueto = task[2]
            self.add_task(None, task_text,task_category,task_dueto, True)



        self.bind("<Return>", self.add_task)
        self.bind("<Configure>", self.on_frame_configure)
        self.bind_all("<MouseWheel>", self.mouse_scroll)
        self.bind_all("<Button-4>", self.mouse_scroll)
        self.bind_all("<Button-5>", self.mouse_scroll)
        self.tasks_canvas.bind("<Configure>", self.task_width)

    def add_task(self, event=None, task_text=None,task_category=None,task_dueto=None, from_db=False):
        if not task_text:
            input_data=self.task_create.get(1.0, tk.END).strip()
            if input_data.count("/")!=2:
                msg.showinfo("Error", "    Use format:\nname/category/dueto")
                self.task_create.delete(1.0, tk.END)
                return
            task_text,task_category,task_dueto = input_data.split('/')
            task_text=task_text.strip()
            task_category=task_category.strip()
            task_dueto=task_dueto.strip()

            if task_category=="":
            	task_category="default"
            if task_dueto=="":
            	task_dueto="default"


            for task in self.tasks:
            	if task["task_label"].cget("text")==task_text:
            		msg.showinfo("Error", "There is already a task with such name")
            		self.task_create.delete(1.0, tk.END)
            		return



        if len(task_text) > 0:
            new_task_frame = tk.Frame(self.FRAME_tasks,pady=10)
            new_task = tk.Label(new_task_frame, text=task_text)
            new_task_dueto = tk.Label(new_task_frame,text=task_dueto)
            new_task_category = tk.Label(new_task_frame,text=task_category)


            new_task_triplet={"frame":new_task_frame,"task_label":new_task,"due_to_label":new_task_dueto,"category":new_task_category}

            if from_db:
            	self.set_task_colour(len(self.tasks),new_task_triplet)
            new_task_frame.bind("<Button-1>", self.remove_task)

            new_task_triplet["frame"].pack(side=tk.TOP,fill=tk.X)
            new_task_triplet["task_label"].pack(side=tk.LEFT,padx=(10,0))
            new_task_triplet["due_to_label"].pack(side=tk.RIGHT,padx=(0,20))
            new_task_triplet["category"].pack(side=tk.LEFT,padx=(5,0))


            self.tasks.append(new_task_triplet)

            if not from_db:
                self.save_task(task_text,task_category,task_dueto)
                self.set_task_colour(len(self.tasks),new_task_triplet)


        self.task_create.delete(1.0, tk.END)

    def remove_task(self, event):
        task_frame = event.widget
        for task_dictionary in self.tasks:
            if task_dictionary["frame"]==task_frame:
                task_dic=task_dictionary

        if msg.askyesno("Really Delete?", "Delete " + task_dic["task_label"].cget("text") + "?"):
            delete_task_query = "DELETE FROM tasks WHERE name=?"
            delete_task_data = (task_dic["task_label"].cget("text"),)
            for widget in task_dic.values():
               	widget.destroy()
            self.tasks.remove(task_dic)

            self.runQuery(delete_task_query, delete_task_data)

            self.recolour_tasks()


    def recolour_tasks(self):
        for index, task in enumerate(self.tasks):
            self.set_task_colour(index, task)

    def set_task_colour(self, position, task):
        _, task_style_choice = divmod(position, 2)

        task_name=task["task_label"].cget("text")
        conn = sqlite3.connect("tasks.db")
        cursor = conn.cursor()

        cursor.execute("SELECT name,category,dueto FROM tasks WHERE name=?",(task_name,))

        category_name=cursor.fetchone()[1]


        cursor.execute("SELECT name,color FROM categories WHERE name=?",(category_name,))
        color=cursor.fetchone()
        if not color:
        	color="lightgrey"
        else:
        	color=color[1]
        conn.close()

        
        my_scheme_choice = self.colour_schemes[task_style_choice]

        task["frame"].configure(bg=color)
        task["task_label"].configure(bg=color)
        task["due_to_label"].configure(bg=color)

        task["task_label"].configure(fg=my_scheme_choice["fg"])
        task["due_to_label"].configure(fg=my_scheme_choice["fg"])

    def on_frame_configure(self, event=None):
        self.tasks_canvas.configure(scrollregion=self.tasks_canvas.bbox("all"))

    def task_width(self, event):
        canvas_width = event.width
        self.tasks_canvas.itemconfig(self.canvas_frame, width = canvas_width)

    def mouse_scroll(self, event):
        if event.delta:
            self.tasks_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        else:
            if event.num == 5:
                move = 1
            else:
                move = -1

            self.tasks_canvas.yview_scroll(move, "units")

   




    def save_task(self, task_name,category,dueto):
        insert_task_query = "INSERT INTO tasks(name,category,dueto) VALUES (?,?,?)"
        insert_task_data = (task_name,category,dueto)
        self.runQuery(insert_task_query, insert_task_data)

    def load_tasks(self):
        load_tasks_query = "SELECT name,category,dueto FROM tasks"
        my_tasks = self.runQuery(load_tasks_query, receive=True)

        return my_tasks

    #needs to be called before init
    @staticmethod
    def runQuery(sql, data=None, receive=False):
        #connect to database file
        conn = sqlite3.connect("tasks.db")
        #create cursor
        cursor = conn.cursor()
        #if we gave data,execute it
        if data:
            cursor.execute(sql, data)
        else:
            cursor.execute(sql)

        #returns data if we chose receive
        if receive:
            return cursor.fetchall()
        #if not we save changes
        else:
            conn.commit()
        #closes db
        conn.close()


    #called before init
    @staticmethod
    def firstTimeDB():
        #creates table
        create_tables = """CREATE TABLE tasks (id INTEGER PRIMARY KEY,name TEXT,
                           category TEXT, dueto TEXT)"""
        Todo.runQuery(create_tables)

        create_color_table = """CREATE TABLE categories(name TEXT, color TEXT)"""
        Todo.runQuery(create_color_table)

        #added default task here
        default_task_query = "INSERT INTO tasks(name,category,dueto) VALUES (?,?,?)"
        default_task_data = ("--- Add Items Here ---","default","default")
        Todo.runQuery(default_task_query, default_task_data)

        default_category_query = "INSERT INTO categories(name,color) VALUES (?,?)"
        default_category_data = ("default","lightgrey")
        Todo.runQuery(default_category_query,default_category_data)


    def new_category_window(self):
        t=tk.Toplevel(self)
        t.wm_title("Add new category")
        t.wm_geometry("100x200")
        name_label = tk.Label(t,text="Enter name:")
        name_input = tk.Text(t, height=3,width=20, bg="white", fg="black")
        color_label = tk.Label(t,text="Color")
        color_choose_button = tk.Button(t, text="Choose Color", command=lambda :self.get_color(color_label,name_input))
        

        
        add_button = tk.Button(t,text="Add",command=lambda :self.add_category(name_input,color_label,t))


        name_label.pack(side="top")
        name_input.pack(side="top")
        color_label.pack(side="top")
        color_choose_button.pack(side="top")
        add_button.pack(side="top")

        name_input.focus_set()

        category=name_input.get(1.0, tk.END).strip()
       

    def get_color(self,color_label,name_input):
        color=askcolor()
        color_label.configure(bg=color[1])
        name_input.focus_set()    	

    def add_category(self,name_input,color_label,t):
        category=name_input.get(1.0, tk.END).strip()


        conn = sqlite3.connect("tasks.db")
        cursor = conn.cursor()

        cursor.execute("SELECT name,color FROM categories WHERE name=?",(category,))

        category_fetch=cursor.fetchone()
        if not category_fetch:
            cursor.execute("SELECT name,color FROM categories WHERE color=?",(color_label.cget("bg"),))

            category_fetch=cursor.fetchone()

        conn.close()
        if category_fetch:
        	msg.showinfo("Error", "Category with this name or color alreay exists")
        	return



        color=color_label.cget("bg")
        add_category_sql="""INSERT INTO categories(name,color) VALUES (?,?)"""
        add_category_data=(category,color)
        Todo.runQuery(add_category_sql,add_category_data)
        t.destroy()
        self.recolour_tasks()


    def display_by_categories_window(self):
        t=tk.Toplevel(self)
        t.wm_title("Display by category")
        t.wm_geometry("100x200")
        name_label = tk.Label(t,text="Choose category:")

        category_choose_button = tk.Button(t, text="Choose category", command=lambda :self.display_category(variable))
        
        #dictionary of categories
        load_categories_query = "SELECT name,color FROM categories"
        categories = self.runQuery(load_categories_query, receive=True)
        categories_lst=[]
        for category in categories:
        	categories_lst.append(category[0])

        variable = tk.StringVar(t)
        variable.set("default")
        tuple_added=(t,variable)+tuple(categories_lst)
        w = tk.OptionMenu(t,variable,*tuple(categories_lst))

        name_label.pack(side="top")
        w.pack()
        category_choose_button.pack(side="top")
         

    def display_category(self,variable):
        category_name=variable.get()
        t=tk.Toplevel(self)
        t.wm_title("Display by category: "+category_name)
        t.wm_geometry("400x700")


        conn = sqlite3.connect("tasks.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name,category,dueto FROM tasks WHERE category = '{}'".format(category_name))

        

        my_tasks = cursor.fetchall()
        conn.close()

        for task_tuple in my_tasks:

            FRAME_tasks = tk.Frame(t)

            new_task_frame = tk.Frame(FRAME_tasks,pady=10)
            new_task = tk.Label(new_task_frame, text=task_tuple[0])
            new_task_dueto = tk.Label(new_task_frame,text=task_tuple[2])
            new_task_category = tk.Label(new_task_frame,text=task_tuple[1])


            new_task_triplet={"frame":new_task_frame,"task_label":new_task,"due_to_label":new_task_dueto,"category":new_task_category}

           
            self.set_task_colour(len(my_tasks),new_task_triplet)
            

            new_task_triplet["frame"].pack(side=tk.TOP,fill=tk.X)
            new_task_triplet["task_label"].pack(side=tk.LEFT,padx=(10,0))
            new_task_triplet["due_to_label"].pack(side=tk.RIGHT,padx=(0,20))
            new_task_triplet["category"].pack(side=tk.LEFT,padx=(5,0))
            FRAME_tasks.pack(fill=tk.BOTH)


if __name__ == "__main__":
    if not os.path.isfile("tasks.db"):
        Todo.firstTimeDB()
    todo = Todo()
    todo.mainloop()