import tkinter as tk  # Importa a biblioteca tkinter para criar interfaces gráficas
from tkinter import filedialog  # Importa a função filedialog da biblioteca tkinter para abrir janelas de seleção de arquivo
from PIL import Image, ImageTk  # Importa as classes Image e ImageTk do módulo PIL para manipulação de imagens
import cv2  # Importa a biblioteca OpenCV para processamento de imagem
import numpy as np  # Importa a biblioteca NumPy para operações numéricas
import math  # Importa o módulo math para operações matemáticas

class ImageSelectorApp:
    def __init__(self, root):
        self.root = root  # Define a janela principal como o objeto root
        self.root.title("Selecione uma imagem")  # Define o título da janela

        # Configuração do frame para a imagem
        self.image_frame = tk.Frame(root, width=600, height=400)  # Cria um frame para exibir a imagem
        self.image_frame.grid(row=0, column=0, padx=10, pady=10)  # Posiciona o frame na janela principal

        self.canvas = tk.Canvas(self.image_frame, width=600, height=400)  # Cria um canvas para desenhar a imagem
        self.canvas.pack(fill=tk.BOTH, expand=True)  # Adiciona o canvas ao frame e configura para preencher o espaço disponível

        self.points = []  # Lista para armazenar os pontos selecionados pelo usuário
        self.lines = []  # Lista para armazenar as linhas desenhadas pelo usuário
        self.image = None  # Variável para armazenar a imagem carregada
        self.closed_polygon = False  # Flag para indicar se o polígono foi fechado

        # Botões e rótulos para interação com o usuário
        self.load_button = tk.Button(root, text="Carregar imagem", command=self.load_image)
        self.load_button.grid(row=1, column=0, padx=10, pady=10)
        self.done_button = tk.Button(root, text="Concluído", command=self.finish_selection)
        self.status_label = tk.Label(root, text="Selecione a área", fg="black", font=("Arial", 16))

        # Escala de conversão
        self.scale_conversion = 0.052  # m²/pixel

        self.area_label = tk.Label(root, text="", fg="black", font=("Arial", 16))
        self.slope_label = tk.Label(root, text="", fg="black", font=("Arial", 16))

    def load_image(self):
        file_path = filedialog.askopenfilename()  # Abre uma janela de seleção de arquivo e obtém o caminho do arquivo selecionado
        if file_path:
            self.image = cv2.imread(file_path)  # Carrega a imagem usando o OpenCV
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)  # Converte de BGR para RGB
            self.image = self.resize_image(self.image, (600, 400))  # Redimensiona a imagem para caber no canvas
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(self.image))  # Converte a imagem para um formato compatível com o tkinter

            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)  # Desenha a imagem no canvas

            self.load_button.grid_forget()  # Remove o botão de carregar imagem
            self.done_button.grid(row=2, column=0, padx=10, pady=10)  # Adiciona o botão de conclusão
            self.status_label.grid(row=3, column=0, padx=10, pady=10)  # Adiciona o rótulo de status

            self.canvas.bind("<Button-1>", self.add_point)  # Associa a função add_point ao evento de clique do mouse no canvas

    def add_point(self, event):
        if self.closed_polygon:
            return

        x, y = event.x, event.y  # Obtém as coordenadas do ponto onde ocorreu o clique do mouse
        self.points.append((x, y))  # Adiciona as coordenadas à lista de pontos
        self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="red")  # Desenha um ponto vermelho no canvas

        if len(self.points) > 1:
            prev_point = self.points[-2]
            self.canvas.create_line(prev_point[0], prev_point[1], x, y, fill="blue")  # Desenha uma linha azul entre os dois pontos

    def finish_selection(self):
        if len(self.points) < 3:
            self.status_label.config(text="Área não encontrada", fg="red")
        elif not self.closed_polygon:
            self.connect_first_and_last_points()  # Conecta o primeiro e o último ponto automaticamente
            self.status_label.config(text="Telhado selecionado", fg="green")
            self.detect_roof_slope()  # Detecta a inclinação do telhado
            self.calculate_area()  # Calcula a área do telhado

    def connect_first_and_last_points(self):
        if self.distance(self.points[0], self.points[-1]) < 10:
            first_point = self.points[0]
            last_point = self.points[-1]
            self.canvas.create_line(last_point[0], last_point[1], first_point[0], first_point[1], fill="blue")
            self.closed_polygon = True

    def detect_roof_slope(self):
        # Extrai coordenadas das linhas do telhado
        roof_lines = []
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            roof_lines.append([(x1, y1), (x2, y2)])

        # Calcula a inclinação de cada linha do telhado
        slopes = []
        for line in roof_lines:
            x1, y1 = line[0]
            x2, y2 = line[1]
            angle = math.atan2(y2 - y1, x2 - x1) * 180 / math.pi
            slopes.append(angle)

        # Calcula a inclinação média do polígono
        avg_slope = np.mean(slopes)
        self.slope_label.config(text=f"Inclinação média do telhado: {avg_slope:.2f} graus")

    def calculate_area(self):
        # Calcul

        area_pixels = self.calculate_polygon_area()

        # Converte a área para metros quadrados
        area_meters = area_pixels * self.scale_conversion

        self.area_label.config(text=f"Área do telhado selecionado é: {area_meters:.2f} metros quadrados")

    def calculate_polygon_area(self):
        # Algoritmo de varredura de linha (scanline)
        min_x = min(point[0] for point in self.points)
        max_x = max(point[0] for point in self.points)
        min_y = min(point[1] for point in self.points)
        max_y = max(point[1] for point in self.points)

        area = 0
        for y in range(min_y, max_y):
            intersections = []
            for i in range(len(self.points)):
                p1 = self.points[i]
                p2 = self.points[(i + 1) % len(self.points)]
                if p1[1] <= y < p2[1] or p2[1] <= y < p1[1]:
                    if p1[1] != p2[1]:
                        x_intersection = p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                        intersections.append(x_intersection)
            intersections.sort()
            for i in range(0, len(intersections), 2):
                area += intersections[i+1] - intersections[i]

        return area

    def reset_selection(self):
        self.canvas.delete("all")  # Remove todos os objetos desenhados no canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)  # Desenha a imagem no canvas novamente
        self.draw_points()  # Redesenha os pontos após a reinicialização
        self.closed_polygon = False  # Reseta a flag de polígono fechado
        self.status_label.config(text="Selecione a área", fg="black")  # Atualiza o rótulo de status

    def resize_image(self, image, new_size):
        # Obtém as dimensões originais da imagem
        original_size = image.shape[1], image.shape[0]
        # Calcula a proporção de redimensionamento
        ratio = max(new_size[0] / original_size[0], new_size[1] / original_size[1])
        # Calcula o novo tamanho mantendo a proporção original
        new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
        # Redimensiona a imagem usando a interpolação de Lanczos
        resized_image = cv2.resize(image, new_size, interpolation=cv2.INTER_LANCZOS4)
        return resized_image

    def distance(self, point1, point2):
        x1, y1 = point1
        x2, y2 = point2
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

if __name__ == "__main__":
    root = tk.Tk()  # Cria a janela principal
    app = ImageSelectorApp(root)  # Cria uma instância da classe ImageSelectorApp
    app.area_label.grid(row=4, column=0, padx=10, pady=10)  # Adiciona o rótulo da área na janela
    app.slope_label.grid(row=5, column=0, padx=10, pady=10)  # Adiciona o rótulo da inclinação na janela
    root.mainloop()  # Inicia o loop principal da interface gráfica

