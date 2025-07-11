import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import pypdf
import re
import os
from threading import Thread
import json
from datetime import datetime

PADRAO_VALOR = r"R\$ ?(-?\d{1,3}(?:\.\d{3})*,\d{2})"

class ExtratorFinanceiro:
    def __init__(self, root):
        self.root = root
        self.root.title("📊 Extrator Financeiro Premium")
        self.root.geometry("1000x800")
        
        # Configuração inicial
        self.setup_estilos()
        self.carregar_configuracoes()
        
        # Variáveis de controle
        self.arquivos_pendentes = []
        self.processando = False
        self.historico = self.carregar_historico()
        self.loading_frames = []
        self.current_loading_frame = 0
        self.loading_animation_id = None
        
        # Interface
        self.criar_interface()
        self.atualizar_interface()
    
    def setup_estilos(self):
        """Configura os estilos visuais da aplicação"""
        self.fonte_principal = font.Font(family="Segoe UI", size=10)
        self.fonte_destaque = font.Font(family="Segoe UI", size=10, weight="bold")
        self.fonte_titulo = font.Font(family="Segoe UI", size=12, weight="bold")
        
        style = ttk.Style()
        style.configure("TFrame", background="#f5f5f5")
        style.configure("TButton", font=self.fonte_principal, padding=6)
        style.configure("TLabel", font=self.fonte_principal)
        style.configure("Treeview.Heading", font=self.fonte_titulo)
        style.configure("Treeview", font=self.fonte_principal, rowheight=25)
        style.map("TButton", background=[("active", "#e0e0e0")])
        
        # Configura estilo para o botão de processamento
        style.configure("Green.TButton", 
                      foreground="black",  # Changed to black font
                      background="#4CAF50",
                      font=self.fonte_principal,
                      padding=6)
        style.map("Green.TButton",
                background=[("active", "#45a049")],
                foreground=[("active", "black")])  # Keep black when active
    
    def carregar_configuracoes(self):
        """Carrega configurações persistentes"""
        self.config = {
            "descricao": tk.StringVar(value="Débito por dívida Imposto interestadual"),
            "ultimo_diretorio": os.path.expanduser("~")
        }
    
    def criar_interface(self):
        """Cria todos os componentes da interface"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Painel de controle
        self.criar_painel_controle(main_frame)
        
        # Painel de arquivos
        self.criar_painel_arquivos(main_frame)
        
        # Painel de resultados
        self.criar_painel_resultados(main_frame)
        
        # Barra de status
        self.criar_barra_status(main_frame)
        
        # Carrega frames da animação de loading
        self.carregar_frames_animacao()
    
    def carregar_frames_animacao(self):
        """Prepara os frames da animação de loading"""
        self.loading_frames = [
            "⚡ Processando ⚡", 
            "⚡ Processando. ⚡",
            "⚡ Processando.. ⚡",
            "⚡ Processando... ⚡"
        ]
    
    def iniciar_animacao_loading(self):
        """Inicia a animação de loading no botão de processamento"""
        self.current_loading_frame = 0
        self.animar_loading()
    
    def animar_loading(self):
        """Anima o botão de processamento"""
        if self.processando:
            texto = self.loading_frames[self.current_loading_frame]
            self.btn_processar.config(text=texto)
            self.current_loading_frame = (self.current_loading_frame + 1) % len(self.loading_frames)
            self.loading_animation_id = self.root.after(300, self.animar_loading)
    
    def parar_animacao_loading(self):
        """Para a animação de loading"""
        if self.loading_animation_id:
            self.root.after_cancel(self.loading_animation_id)
            self.loading_animation_id = None
        self.btn_processar.config(text="⚡ Processar Selecionados")
    
    def criar_painel_controle(self, parent):
        """Cria o painel superior com controles"""
        frame = ttk.LabelFrame(parent, text=" Controles ", padding=15)
        frame.pack(fill=tk.X, pady=(0, 15))
        
        # Botões principais
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            btn_frame,
            text="➕ Adicionar PDFs",
            command=self.adicionar_arquivos,
            style="Green.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="🗑️ Limpar Lista",
            command=self.limpar_lista
        ).pack(side=tk.LEFT, padx=5)
        
        # Configuração de padrão
        ttk.Label(btn_frame, text="Padrão de busca:").pack(side=tk.LEFT, padx=(20,5))
        ttk.Entry(
            btn_frame,
            textvariable=self.config["descricao"],
            width=40
        ).pack(side=tk.LEFT, expand=True, fill=tk.X)
    
    def criar_painel_arquivos(self, parent):
        """Cria o painel de listagem de arquivos"""
        frame = ttk.LabelFrame(parent, text=" Arquivos para Processar ", padding=15)
        frame.pack(fill=tk.BOTH, pady=(0, 15), expand=True)
        
        # Lista de arquivos
        self.lista_arquivos = ttk.Treeview(
            frame,
            columns=("status", "arquivo", "caminho"),
            show="headings",
            selectmode="extended",
            height=8
        )
        
        # Configura colunas
        self.lista_arquivos.heading("status", text="Status")
        self.lista_arquivos.heading("arquivo", text="Arquivo")
        self.lista_arquivos.heading("caminho", text="Caminho")
        
        self.lista_arquivos.column("status", width=80, anchor=tk.CENTER)
        self.lista_arquivos.column("arquivo", width=200)
        self.lista_arquivos.column("caminho", width=400)
        
        # Scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.lista_arquivos.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.lista_arquivos.xview)
        self.lista_arquivos.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Layout
        self.lista_arquivos.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Botão de processamento
        self.btn_processar = ttk.Button(
            frame,
            text="⚡ Processar Selecionados",
            command=self.iniciar_processamento,
            style="Green.TButton"
        )
        self.btn_processar.grid(row=2, column=0, columnspan=2, pady=(10,0), sticky="ew")
    
    def criar_painel_resultados(self, parent):
        """Cria o painel de exibição de resultados"""
        frame = ttk.LabelFrame(parent, text=" Histórico de Processamento ", padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Tabela de resultados
        self.tabela_resultados = ttk.Treeview(
            frame,
            columns=("data", "arquivo", "valor"),
            show="headings",
            height=12
        )
        
        # Configura colunas
        colunas = {
            "data": {"text": "Data/Hora", "width": 120},
            "arquivo": {"text": "Arquivo", "width": 200},
            "valor": {"text": "Valor (R$)", "width": 100}
        }
        
        for col, config in colunas.items():
            self.tabela_resultados.heading(col, text=config["text"])
            self.tabela_resultados.column(col, width=config["width"], anchor=tk.CENTER if col == "valor" else tk.W)
        
        # Scrollbar
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tabela_resultados.yview)
        self.tabela_resultados.configure(yscrollcommand=vsb.set)
        
        # Layout
        self.tabela_resultados.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configura tags para formatação
        self.tabela_resultados.tag_configure("valor", foreground="green")
        self.tabela_resultados.tag_configure("erro", foreground="red")
    
    def criar_barra_status(self, parent):
        """Cria a barra de status inferior"""
        self.status_var = tk.StringVar(value="Pronto. Adicione arquivos PDF para começar.")
        
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(10,0))
        
        self.progresso = ttk.Progressbar(
            frame,
            orient=tk.HORIZONTAL,
            mode="determinate",
            length=200
        )
        self.progresso.pack(side=tk.LEFT, padx=(0,10))
        
        ttk.Label(
            frame,
            textvariable=self.status_var,
            font=self.fonte_principal,
            relief=tk.SUNKEN,
            padding=5
        ).pack(side=tk.LEFT, expand=True, fill=tk.X)
    
    def adicionar_arquivos(self):
        """Adiciona arquivos PDF para processamento"""
        arquivos = filedialog.askopenfilenames(
            title="Selecione os arquivos PDF",
            initialdir=self.config["ultimo_diretorio"],
            filetypes=[("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")]
        )
        
        if arquivos:
            self.config["ultimo_diretorio"] = os.path.dirname(arquivos[0])
            novos_arquivos = 0
            
            for arquivo in arquivos:
                if arquivo not in self.arquivos_pendentes:
                    self.arquivos_pendentes.append(arquivo)
                    novos_arquivos += 1
            
            self.atualizar_interface()
            self.status_var.set(f"Adicionados {novos_arquivos} novo(s) arquivo(s). Total: {len(self.arquivos_pendentes)}")
    
    def limpar_lista(self):
        """Remove todos os arquivos da lista de processamento"""
        if self.arquivos_pendentes:
            self.arquivos_pendentes = []
            self.atualizar_interface()
            self.status_var.set("Lista de arquivos limpa. Adicione novos arquivos para processar.")
    
    def iniciar_processamento(self):
        """Inicia o processamento dos arquivos selecionados"""
        if not self.arquivos_pendentes:
            messagebox.showwarning("Aviso", "Nenhum arquivo para processar!")
            return
        
        if self.processando:
            messagebox.showwarning("Aviso", "Processamento já em andamento!")
            return
        
        # Prepara interface para processamento
        self.processando = True
        self.atualizar_controles()
        self.progresso["maximum"] = len(self.arquivos_pendentes)
        self.progresso["value"] = 0
        self.iniciar_animacao_loading()
        
        # Inicia thread de processamento
        Thread(target=self.processar_arquivos, daemon=True).start()
    
    def processar_arquivos(self):
        """Processa todos os arquivos na fila"""
        try:
            descricao = self.config["descricao"].get()
            
            for i, arquivo in enumerate(self.arquivos_pendentes):
                try:
                    # Atualiza interface
                    self.status_var.set(f"Processando {i+1}/{len(self.arquivos_pendentes)}: {os.path.basename(arquivo)}")
                    self.progresso["value"] = i + 1
                    self.root.update()
                    
                    # Processa o arquivo
                    resultado = self.processar_arquivo(arquivo, descricao)
                    
                    # Registra no histórico
                    registro = {
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "arquivo": os.path.basename(arquivo),
                        "caminho": arquivo,
                        "valor": resultado["total"],
                        "status": "sucesso"
                    }
                    
                    self.historico.append(registro)
                    
                except Exception as e:
                    registro = {
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "arquivo": os.path.basename(arquivo),
                        "caminho": arquivo,
                        "valor": 0.0,
                        "status": f"erro: {str(e)}"
                    }
                    self.historico.append(registro)
            
            # Finaliza processamento
            self.arquivos_pendentes = []
            self.salvar_historico()
            self.status_var.set("Processamento concluído com sucesso!")
            messagebox.showinfo("Concluído", "Todos os arquivos foram processados!")
            
        except Exception as e:
            self.status_var.set(f"Erro durante o processamento: {str(e)}")
            messagebox.showerror("Erro", f"Ocorreu um erro durante o processamento:\n{str(e)}")
            
        finally:
            self.processando = False
            self.parar_animacao_loading()
            self.atualizar_controles()
            self.atualizar_interface()
    
    def processar_arquivo(self, caminho_pdf, descricao):
        """Processa um único arquivo PDF"""
        try:
            doc = pypdf.PdfReader(caminho_pdf)
            total = 0.0
            
            for pagina in doc.pages:
                texto = pagina.extract_text()
                if not texto:
                    continue
                
                linhas = [linha.strip() for linha in texto.split('\n') if linha.strip()]
                
                for linha in linhas:
                    if descricao in linha:
                        match = re.search(PADRAO_VALOR, linha)
                        if match:
                            valor_str = match.group(1).replace(".", "").replace(",", ".")
                            total += float(valor_str)
            
            return {"total": total, "status": "sucesso"}
            
        except Exception as e:
            raise Exception(f"Erro ao processar {os.path.basename(caminho_pdf)}: {str(e)}")
    
    def atualizar_interface(self):
        """Atualiza toda a interface gráfica"""
        # Limpa as listas
        self.lista_arquivos.delete(*self.lista_arquivos.get_children())
        self.tabela_resultados.delete(*self.tabela_resultados.get_children())
        
        # Atualiza lista de arquivos pendentes
        for i, arquivo in enumerate(self.arquivos_pendentes):
            self.lista_arquivos.insert("", tk.END, values=(
                "Pendente",
                os.path.basename(arquivo),
                arquivo
            ))
        
        # Atualiza histórico de processamento
        for item in sorted(self.historico, key=lambda x: x["data"], reverse=True):
            tag = "erro" if "erro" in item["status"] else "valor"
            self.tabela_resultados.insert("", tk.END, values=(
                item["data"],
                item["arquivo"],
                f"{item['valor']:.2f}" if isinstance(item['valor'], (int, float)) else item['valor']
            ), tags=(tag,))
    
    def atualizar_controles(self):
        """Atualiza o estado dos controles da interface"""
        state = tk.DISABLED if self.processando else tk.NORMAL
        
        for child in self.root.winfo_children():
            if isinstance(child, (ttk.Button, ttk.Entry)):
                child.configure(state=state)
    
    def carregar_historico(self):
        """Carrega o histórico de processamentos anteriores"""
        try:
            if os.path.exists("historico.json"):
                with open("historico.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            messagebox.showwarning("Aviso", f"Erro ao carregar histórico:\n{str(e)}")
        return []
    
    def salvar_historico(self):
        """Salva o histórico de processamentos"""
        try:
            with open("historico.json", "w", encoding="utf-8") as f:
                json.dump(self.historico, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showwarning("Aviso", f"Erro ao salvar histórico:\n{str(e)}")
    
    def on_close(self):
        """Executado ao fechar a aplicação"""
        self.salvar_historico()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ExtratorFinanceiro(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()