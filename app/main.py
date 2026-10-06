"""Чудо Обувь — ДЭ 09.02.07-2-2027"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta, datetime
from PIL import Image, ImageTk
import psycopg2, os

DB = {"host": "localhost", "database": "chudo_shoes",
      "user": "postgres", "password": "8642", "port": "5432"}  # ← пароль
BG, BG2, AC, WARN = "#FFFFFF", "#D2F6E7", "#70B2AF", "#ff8080"
F, FT, FH = ("Calibri", 11), ("Calibri", 16, "bold"), ("Calibri", 14, "bold")
RES = os.path.join(os.path.dirname(__file__), "resources")
PROD = os.path.join(RES, "products")
conn = None


def db():
    return psycopg2.connect(**DB)


def disc(pid, price):
    t = date.today()
    lm = t.replace(day=1) - timedelta(days=1)
    fm = lm.replace(day=1)
    c = conn.cursor()
    c.execute("""SELECT COUNT(*) FROM order_items oi
        JOIN product_sizes ps ON oi.product_size_id=ps.product_size_id
        JOIN orders o ON oi.order_id=o.order_id
        WHERE ps.product_id=%s AND o.order_date BETWEEN %s AND %s""",
              (pid, fm, lm))
    n = c.fetchone()[0]
    c.close()
    return round(price * .75, 2) if n == 0 else round(price, 2)


def catalog(sort="none"):
    c = conn.cursor()
    q = """SELECT p.product_id,p.product_name,c.category_name,m.manufacturer_name,
        p.composition,p.price,p.image_path,COALESCE(SUM(ps.quantity),0)
        FROM products p
        JOIN categories c ON p.category_id=c.category_id
        JOIN manufacturers m ON p.manufacturer_id=m.manufacturer_id
        LEFT JOIN product_sizes ps ON p.product_id=ps.product_id
        GROUP BY p.product_id,c.category_name,m.manufacturer_name"""
    if sort == "asc":
        q += " ORDER BY p.price ASC"
    elif sort == "desc":
        q += " ORDER BY p.price DESC"
    c.execute(q)
    rows = c.fetchall()
    c.close()
    return [{"id": r[0], "n": r[1], "cat": r[2], "man": r[3], "comp": r[4] or "",
             "price": disc(r[0], float(r[5])), "img": r[6], "qty": r[7],
             "lbl": "много" if r[7] > 5 else "мало", "warn": r[7] <= 3}
            for r in rows]


class App:
    def __init__(self, r):
        global conn
        conn = db()
        self.root = r
        r.title("Чудо Обувь")
        r.geometry("1100x750")
        r.configure(bg=BG)
        self.user, self.cart = None, []
        self.login()

    def clr(self):
        for w in self.root.winfo_children():
            w.destroy()

    # ---------- ВХОД ----------
    def login(self):
        self.clr()
        self.cart = []
        f = tk.Frame(self.root, bg=BG2)
        f.place(relx=.5, rely=.5, anchor="center", width=420, height=320)
        tk.Label(f, text="Чудо Обувь", font=("Calibri", 22, "bold"),
                 bg=BG2).pack(pady=(30, 5))
        tk.Label(f, text="Вход в систему", font=F, bg=BG2).pack(pady=(0, 20))
        tk.Label(f, text="Логин:", font=F, bg=BG2).pack(anchor="w", padx=40)
        self.e = tk.Entry(f, font=F, width=30)
        self.e.pack(pady=5, padx=40)
        self.e.bind("<Return>", lambda _: self.do_login())
        tk.Button(f, text="Войти", font=F, bg=AC, fg="white", width=20,
                  command=self.do_login).pack(pady=20)
        tk.Label(f, text="isivanov / papetrov / asidorova",
                 font=("Calibri", 9), bg=BG2, fg="#555").pack()

    def do_login(self):
        lg = self.e.get().strip()
        if not lg:
            messagebox.showerror("Ошибка", "Введите логин!")
            return
        c = conn.cursor()
        c.execute("""SELECT u.user_id,u.last_name,u.first_name,u.middle_name,
            r.role_name FROM users u JOIN roles r ON u.role_id=r.role_id
            WHERE u.login=%s""", (lg,))
        u = c.fetchone()
        c.close()
        if not u:
            messagebox.showerror("Ошибка", "Пользователь не найден!")
            return
        self.user = {"id": u[0], "ln": u[1], "fn": u[2], "mn": u[3], "role": u[4]}
        self.main()

    # ---------- КАТАЛОГ ----------
    def main(self):
        self.clr()
        top = tk.Frame(self.root, bg=AC, height=55)
        top.pack(fill="x")
        top.pack_propagate(False)
        try:
            self.lg = ImageTk.PhotoImage(Image.open(
                os.path.join(RES, "Чудо Обувь.png")).resize((40, 40)))
            tk.Label(top, image=self.lg, bg=AC).pack(side="left", padx=10)
        except Exception:
            pass
        tk.Label(top, text="Чудо Обувь", font=FT, bg=AC, fg="white").pack(side="left")
        fio = f"{self.user['ln']} {self.user['fn']}" + (
            f" {self.user['mn']}" if self.user['mn'] else "")
        tk.Label(top, text=fio, font=F, bg=AC, fg="white").pack(side="right", padx=15)
        tk.Button(top, text="Выход", font=("Calibri", 10), bg="#e74c3c",
                  fg="white", command=self.login).pack(side="right", padx=5)
        tk.Button(top, text="🛒 Корзина", font=F, bg=BG, fg=AC,
                  command=self.cart_win).pack(side="right", padx=5)
        if self.user["role"] in ("Администратор", "Менеджер"):
            tk.Button(top, text="📋 Заказы", font=F, bg=BG, fg=AC,
                      command=self.orders_win).pack(side="right", padx=5)

        fl = tk.Frame(self.root, bg=BG2, pady=10)
        fl.pack(fill="x")
        tk.Label(fl, text="Поиск:", font=F, bg=BG2).grid(row=0, column=0, padx=(10, 5))
        self.s = tk.StringVar()
        self.s.trace_add("write", lambda *_: self.refresh())
        tk.Entry(fl, textvariable=self.s, font=F, width=20).grid(row=0, column=1)
        c = conn.cursor()
        c.execute("SELECT category_name FROM categories ORDER BY category_name")
        cats = [x[0] for x in c.fetchall()]
        c.close()
        tk.Label(fl, text="Категория:", font=F, bg=BG2).grid(row=0, column=2, padx=(20, 5))
        self.ct = tk.StringVar(value="Все категории")
        cb = ttk.Combobox(fl, textvariable=self.ct, values=["Все категории"] + cats,
                          state="readonly", width=18)
        cb.grid(row=0, column=3, padx=5)
        cb.bind("<<ComboboxSelected>>", lambda _: self.refresh())
        tk.Label(fl, text="Сортировка:", font=F, bg=BG2).grid(row=0, column=4, padx=(20, 5))
        self.so = tk.StringVar(value="Без сортировки")
        cb2 = ttk.Combobox(fl, textvariable=self.so, state="readonly", width=18,
                           values=["Без сортировки", "Цена: по возрастанию",
                                   "Цена: по убыванию"])
        cb2.grid(row=0, column=5, padx=5)
        cb2.bind("<<ComboboxSelected>>", lambda _: self.refresh())

        cv = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(self.root, orient="vertical", command=cv.yview)
        self.fr = tk.Frame(cv, bg=BG)
        self.fr.bind("<Configure>", lambda _: cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0, 0), window=self.fr, anchor="nw")
        cv.configure(yscrollcommand=sb.set)
        cv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        cv.bind_all("<MouseWheel>", lambda e: cv.yview_scroll(int(-e.delta / 120), "units"))
        self.refresh()

    def refresh(self):
        for w in self.fr.winfo_children():
            w.destroy()
        so = "asc" if self.so.get() == "Цена: по возрастанию" else (
            "desc" if self.so.get() == "Цена: по убыванию" else "none")
        for it in catalog(so):
            t = self.s.get().lower()
            if t and t not in it["n"].lower() and t not in it["comp"].lower():
                continue
            if self.ct.get() != "Все категории" and it["cat"] != self.ct.get():
                continue
            self.card(it)

    def card(self, it):
        bg = WARN if it["warn"] else BG
        c = tk.Frame(self.fr, bg=bg, relief="solid", bd=1)
        c.pack(fill="x", padx=10, pady=5)
        imf = tk.Frame(c, bg=bg, width=110, height=110)
        imf.pack(side="left", padx=10, pady=10)
        imf.pack_propagate(False)
        try:
            p = os.path.join(PROD, it["img"] or "")
            if not it["img"] or not os.path.exists(p):
                p = os.path.join(RES, "picture.png")
            ph = ImageTk.PhotoImage(Image.open(p).resize((100, 100)))
            lb = tk.Label(imf, image=ph, bg=bg)
            lb.image = ph
            lb.pack()
        except Exception:
            tk.Label(imf, text="[нет фото]", bg=bg).pack()
        inf = tk.Frame(c, bg=bg)
        inf.pack(side="left", fill="both", expand=True, padx=10)
        tk.Label(inf, text=f"{it['man']} | {it['n']}", font=FH, bg=bg,
                 anchor="w", wraplength=650, justify="left").pack(fill="x", pady=(5, 2))
        tk.Label(inf, text=f"Категория: {it['cat']}", font=F, bg=bg,
                 anchor="w").pack(fill="x")
        tk.Label(inf, text=f"Количество: {it['lbl']}", font=F, bg=bg,
                 anchor="w").pack(fill="x")
        tk.Label(inf, text=f"Состав: {it['comp'][:90]}...", font=("Calibri", 10),
                 bg=bg, anchor="w", wraplength=650, justify="left").pack(fill="x")
        tk.Label(c, text=f"{it['price']:.2f} ₽", font=("Calibri", 16, "bold"),
                 bg=bg, fg="#c0392b" if it["warn"] else "#000").pack(side="right", padx=20)
        for w in [c, imf, inf] + list(inf.winfo_children()):
            w.bind("<Button-1>", lambda _, pid=it["id"]: self.view(pid))
            w.configure(cursor="hand2")

    # ---------- ПРОСМОТР ТОВАРА ----------
    def view(self, pid):
        w = tk.Toplevel(self.root)
        w.title("Просмотр товара")
        w.geometry("700x650")
        w.configure(bg=BG)
        tk.Button(w, text="← Назад", font=F, bg=AC, fg="white",
                  command=w.destroy).pack(anchor="nw", padx=10, pady=10)
        c = conn.cursor()
        c.execute("""SELECT p.product_name,c.category_name,m.manufacturer_name,
            p.composition,p.description,p.price,p.image_path
            FROM products p
            JOIN categories c ON p.category_id=c.category_id
            JOIN manufacturers m ON p.manufacturer_id=m.manufacturer_id
            WHERE p.product_id=%s""", (pid,))
        p = c.fetchone()
        c.execute("""SELECT ps.product_size_id,s.size_value,ps.quantity
            FROM product_sizes ps JOIN sizes s ON ps.size_id=s.size_id
            WHERE ps.product_id=%s AND ps.quantity>0 ORDER BY s.size_value""", (pid,))
        sz = c.fetchall()
        c.close()
        if not p:
            w.destroy()
            return
        tk.Label(w, text=f"{p[2]} | {p[0]}", font=("Calibri", 18, "bold"), bg=BG).pack(pady=10)
        try:
            ph = ImageTk.PhotoImage(Image.open(os.path.join(PROD, p[6])).resize((200, 200)))
            lb = tk.Label(w, image=ph, bg=BG)
            lb.image = ph
            lb.pack()
        except Exception:
            pass
        dp = disc(pid, float(p[5]))
        info = tk.Frame(w, bg=BG)
        info.pack(pady=10)
        for lab, val in [("Категория:", p[1]), ("Производство:", p[2]),
                         ("Состав:", p[3] or "—"), ("Описание:", p[4] or "—"),
                         ("Цена со скидкой:", f"{dp:.2f} ₽")]:
            r = tk.Frame(info, bg=BG)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=lab, font=("Calibri", 11, "bold"), bg=BG,
                     width=18, anchor="w").pack(side="left")
            tk.Label(r, text=str(val)[:80], font=F, bg=BG, anchor="w",
                     wraplength=400, justify="left").pack(side="left")
        of = tk.Frame(w, bg=BG2, pady=15)
        of.pack(fill="x", padx=20, pady=10)
        tk.Label(of, text="Размер:", font=F, bg=BG2).pack(side="left", padx=5)
        opts = [f"{x[1]} (в наличии: {x[2]})" for x in sz]
        sv = tk.StringVar()
        ttk.Combobox(of, textvariable=sv, values=opts, state="readonly",
                     width=22).pack(side="left", padx=5)
        tk.Label(of, text="Количество:", font=F, bg=BG2).pack(side="left", padx=5)
        qv = tk.StringVar(value="1")
        tk.Spinbox(of, from_=1, to=100, textvariable=qv, width=5,
                   font=F).pack(side="left", padx=5)

        def add():
            if not sv.get():
                messagebox.showwarning("Внимание", "Выберите размер!")
                return
            try:
                q = int(qv.get())
                if q <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректное количество!")
                return
            i = opts.index(sv.get())
            ps_id, szv, avail = sz[i]
            if q > avail:
                messagebox.showerror("Ошибка", f"Доступно: {avail}")
                return
            self.cart.append({"ps": ps_id, "n": p[0], "man": p[2],
                              "sz": szv, "q": q, "pr": dp})
            messagebox.showinfo("Успех", f"Добавлено!\n{p[0]}, {szv}, {q} шт.")
            w.destroy()

        tk.Button(of, text="Добавить в заказ", font=F, bg=AC, fg="white",
                  command=add).pack(side="left", padx=20)

    # ---------- КОРЗИНА ----------
    def cart_win(self):
        w = tk.Toplevel(self.root)
        w.title("Корзина")
        w.geometry("800x500")
        w.configure(bg=BG)
        tk.Button(w, text="← Назад", font=F, bg=AC, fg="white",
                  command=w.destroy).pack(anchor="nw", padx=10, pady=10)
        tk.Label(w, text="Корзина", font=("Calibri", 18, "bold"), bg=BG).pack(pady=5)
        cols = ("Товар", "Размер", "Кол-во", "Цена", "Сумма")
        tree = ttk.Treeview(w, columns=cols, show="headings", height=10)
        for x in cols:
            tree.heading(x, text=x)
            tree.column(x, width=140)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def fill():
            for i in tree.get_children():
                tree.delete(i)
            for i, it in enumerate(self.cart):
                tree.insert("", "end", iid=str(i),
                            values=(it["n"], it["sz"], it["q"],
                                    f"{it['pr']:.2f}", f"{it['pr'] * it['q']:.2f}"))
        fill()
        tot = sum(i["pr"] * i["q"] for i in self.cart)
        tk.Label(w, text=f"ИТОГО: {tot:.2f} ₽", font=("Calibri", 14, "bold"),
                 bg=BG).pack(pady=5)
        bf = tk.Frame(w, bg=BG)
        bf.pack(pady=10)

        def rm():
            s = tree.selection()
            if not s:
                return
            del self.cart[int(s[0])]
            fill()

        def checkout():
            if not self.cart:
                messagebox.showwarning("Внимание", "Корзина пуста!")
                return
            c = conn.cursor()
            try:
                c.execute("""INSERT INTO orders (order_date,client_last_name,
                    client_first_name,client_middle_name,total_amount)
                    VALUES (%s,%s,%s,%s,%s) RETURNING order_id""",
                          (date.today(), self.user['ln'], self.user['fn'],
                           self.user['mn'], tot))
                oid = c.fetchone()[0]
                for it in self.cart:
                    c.execute("""INSERT INTO order_items (order_id,product_size_id,
                        quantity,unit_price) VALUES (%s,%s,%s,%s)""",
                              (oid, it["ps"], it["q"], it["pr"]))
                    c.execute("UPDATE product_sizes SET quantity=quantity-%s WHERE product_size_id=%s",
                              (it["q"], it["ps"]))
                conn.commit()
                messagebox.showinfo("Успех", f"Заказ №{oid} оформлен!")
                self.cart = []
                w.destroy()
                self.refresh()
            except Exception as e:
                conn.rollback()
                messagebox.showerror("Ошибка", str(e))

        tk.Button(bf, text="🗑 Удалить", font=F, bg="#e74c3c", fg="white",
                  command=rm).pack(side="left", padx=5)
        tk.Button(bf, text="✅ Оформить", font=F, bg=AC, fg="white",
                  command=checkout).pack(side="left", padx=5)

    # ---------- ЗАКАЗЫ ----------
    def orders_win(self):
        w = tk.Toplevel(self.root)
        w.title("Заказы")
        w.geometry("950x600")
        w.configure(bg=BG)
        tk.Button(w, text="← Назад", font=F, bg=AC, fg="white",
                  command=w.destroy).pack(anchor="nw", padx=10, pady=10)
        tk.Label(w, text="Список заказов", font=("Calibri", 18, "bold"), bg=BG).pack(pady=5)
        cols = ("ID", "Дата", "ФИО", "Сумма")
        tree = ttk.Treeview(w, columns=cols, show="headings", height=15)
        for x in cols:
            tree.heading(x, text=x)
            tree.column(x, width=200)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def fill():
            for i in tree.get_children():
                tree.delete(i)
            c = conn.cursor()
            c.execute("""SELECT order_id,order_date,
                CONCAT(client_last_name,' ',client_first_name,' ',
                       COALESCE(client_middle_name,'')),total_amount
                FROM orders ORDER BY order_id DESC""")
            for r in c.fetchall():
                tree.insert("", "end", values=r)
            c.close()
        fill()

        def view():
            s = tree.selection()
            if not s:
                return
            oid = tree.item(s[0])["values"][0]
            self.view_order(oid)

        def edit():
            if self.user["role"] != "Администратор":
                messagebox.showerror("Ошибка", "Только Администратор!")
                return
            s = tree.selection()
            if not s:
                return
            oid = tree.item(s[0])["values"][0]
            self.edit_date(oid, fill)

        def rm():
            if self.user["role"] != "Администратор":
                messagebox.showerror("Ошибка", "Только Администратор!")
                return
            s = tree.selection()
            if not s:
                return
            oid = tree.item(s[0])["values"][0]
            if not messagebox.askyesno("Подтверждение", f"Удалить заказ №{oid}?"):
                return
            c = conn.cursor()
            c.execute("DELETE FROM orders WHERE order_id=%s", (oid,))
            conn.commit()
            c.close()
            fill()

        bf = tk.Frame(w, bg=BG)
        bf.pack(pady=10)
        tk.Button(bf, text="👁 Состав", font=F, bg=AC, fg="white",
                  command=view).pack(side="left", padx=5)
        if self.user["role"] == "Администратор":
            tk.Button(bf, text="✏ Дата", font=F, bg=AC, fg="white",
                      command=edit).pack(side="left", padx=5)
            tk.Button(bf, text="🗑 Удалить", font=F, bg="#e74c3c", fg="white",
                      command=rm).pack(side="left", padx=5)

    def view_order(self, oid):
        w = tk.Toplevel(self.root)
        w.title(f"Заказ №{oid}")
        w.geometry("800x450")
        w.configure(bg=BG)
        tk.Button(w, text="← Назад", font=F, bg=AC, fg="white",
                  command=w.destroy).pack(anchor="nw", padx=10, pady=10)
        tk.Label(w, text=f"Состав заказа №{oid}", font=("Calibri", 16, "bold"),
                 bg=BG).pack(pady=5)
        cols = ("Товар", "Размер", "Кол-во", "Цена", "Сумма")
        tree = ttk.Treeview(w, columns=cols, show="headings", height=10)
        for x in cols:
            tree.heading(x, text=x)
            tree.column(x, width=140)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        c = conn.cursor()
        c.execute("""SELECT p.product_name||' ('||m.manufacturer_name||')',
            s.size_value,oi.quantity,oi.unit_price,oi.quantity*oi.unit_price
            FROM order_items oi
            JOIN product_sizes ps ON oi.product_size_id=ps.product_size_id
            JOIN sizes s ON ps.size_id=s.size_id
            JOIN products p ON ps.product_id=p.product_id
            JOIN manufacturers m ON p.manufacturer_id=m.manufacturer_id
            WHERE oi.order_id=%s""", (oid,))
        tot = 0
        for r in c.fetchall():
            tree.insert("", "end", values=r)
            tot += float(r[4])
        c.close()
        tk.Label(w, text=f"ИТОГО: {tot:.2f} ₽", font=("Calibri", 14, "bold"),
                 bg=BG).pack(pady=10)

    def edit_date(self, oid, cb):
        w = tk.Toplevel(self.root)
        w.title("Изменить дату")
        w.geometry("350x180")
        w.configure(bg=BG)
        tk.Label(w, text=f"Заказ №{oid}", font=F, bg=BG).pack(pady=5)
        tk.Label(w, text="Новая дата (ГГГГ-ММ-ДД):", font=F, bg=BG).pack(pady=5)
        e = tk.Entry(w, font=F, width=20)
        e.pack(pady=5)

        def save():
            try:
                datetime.strptime(e.get().strip(), "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат!")
                return
            c = conn.cursor()
            c.execute("UPDATE orders SET order_date=%s WHERE order_id=%s",
                      (e.get().strip(), oid))
            conn.commit()
            c.close()
            cb()
            w.destroy()

        tk.Button(w, text="Сохранить", font=F, bg=AC, fg="white",
                  command=save).pack(pady=10)


if __name__ == "__main__":
    r = tk.Tk()
    App(r)
    r.mainloop()