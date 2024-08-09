import asyncio
import aiohttp
from bs4 import BeautifulSoup
from rx import from_iterable, operators as ops
from tkinter import Tk, Label
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO

class ImageDownloadObservable:
    def __init__(self, total_images=0):
        self._observer = None

    def subscribe(self, observer):
        self._observer = observer

    async def download_images(self, image_info, progress_var, window):
        async with aiohttp.ClientSession() as session:
            total_images = len(image_info)
            progress_increment = 100 / total_images
        
            for index, info in enumerate(image_info, start=1):
                img_url = info['url']
                alt_text = info['alt']

                async with session.get(img_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        if image_data:
                            # Notify progress bar of progress
                            progress_var.set(progress_var.get() + progress_increment)

                            label = tk.Label(window, text=f"Images found: {total_images}")
                            label.place(x=120, y=380)
                        
                            self._observer.on_next({'alt_text': alt_text, 'image_data': image_data})
                    else:
                        self._observer.on_error(f"Error al descargar la imagen {index} con texto alternativo '{alt_text}'")

class ImageDownloadObserver:
    def on_next(self, value):
        alt_text = value['alt_text']
        image_data = value['image_data']
        if image_data:
            print(f"Imagen '{alt_text}' descargada correctamente. Tamaño: {len(image_data)} bytes")
            # Aquí puedes notificar a la ventana principal de la aplicación con image_data
            
    def on_error(self, error):
        print(f"Error: {error}")
        # Maneja los errores de descarga

# Define una función para extraer la información de las imágenes
def extract_image_info(html_content):
    image_info = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    img_tags = soup.find_all('img')
    
    for img_tag in img_tags:
        src = img_tag.get('src')
        alt = img_tag.get('alt', 'No Alt Text')
        
        if src:
            image_info.append({'url': src, 'alt': alt})
    
    return image_info

async def fetch_url(url):
    if(url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    return print('Error no html found')
    else:
        return None  
    
def show_image(info, window):
    response = requests.get(info)

    if response.status_code == 200:
        # Load image from the response content
        img = Image.open(BytesIO(response.content))

        labelWidth = 210
        labelHeight = 210
        img = img.resize((labelWidth, labelHeight))
        
        # Convert the image for Tkinter
        tk_img = ImageTk.PhotoImage(img)

        for widget in window.winfo_children():
            if isinstance(widget, tk.Label):
                widget.destroy()
        
        # Create a Label widget to display the image
        label = tk.Label(window)
        label.image = tk_img
        label.config(image=tk_img)
        label.pack(padx=10, pady=10)

        x_coord = 140
        y_coord = 100
        label.place(x=x_coord, y=y_coord, width=labelWidth, height=labelHeight)  

        window.update_idletasks()
        
    else:
        print("Failed to fetch the image")

def show_selected_image(selected_index, image_info, window):
    if selected_index:
        selected_info = image_info[selected_index[0]]  # Get the selected image info
        show_image(selected_info['url'], window)  # Display the selected image

def create_list(image_info, window):
    # Crear un Listbox para mostrar las URLs
    listbox = tk.Listbox(window, width=40, height=10)

    # Agregar las URLs al Listbox
    for info in image_info:
        listbox.insert(tk.END, info['alt'])

    x_coord = 0
    y_coord = 100
    listbox.place(x=x_coord, y=y_coord, width=120)

    selected_index = listbox.curselection()
    listbox.bind('<<ListboxSelect>>', lambda event: show_selected_image(listbox.curselection(), image_info, window))

async def download(url, progress_var, window, image_download_observable):
    # Simulating a download task
    html_content = await fetch_url(url)
    image_info = extract_image_info(html_content)

    observer = ImageDownloadObserver()
    image_download_observable.subscribe(observer)

    await image_download_observable.download_images(image_info, progress_var, window)

    create_list(image_info, window)

async def on_button_click(entry, progress_var, window, image_download_observable):
    if entry:
        url = entry.get()
        print(f"User input: {url}")
        await download(url, progress_var, window, image_download_observable)

def on_button_click_wrapper(loop, entry, progress_var, window, image_download_observable):
    loop.create_task(on_button_click(entry, progress_var, window, image_download_observable))

def on_window_close(loop, window):
    loop.stop()
    window.destroy()

def main():
    loop = asyncio.get_event_loop()

    image_download_observable = ImageDownloadObservable()

    window = tk.Tk()
    window.title("Image Downloader")
    window.geometry("350x450")
    window.protocol("WM_DELETE_WINDOW", lambda: on_window_close(loop, window))

    entry = tk.Entry(window)
    entry.pack()

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(window, orient="horizontal", length=200, mode="determinate", variable=progress_var)
    progress_bar.place(x=100, y=350)

    submit_button = tk.Button(window, text="Download", command=lambda: on_button_click_wrapper(loop, entry, progress_var, window, image_download_observable))
    submit_button.pack()

    label = tk.Label(window, text="Enter URL:")
    label.place(x=25, y=0)

    def process_tkinter_events():
        try:
            window.update()
        except tk.TclError:
            loop.stop()

        loop.call_soon(process_tkinter_events)

    loop.call_soon(process_tkinter_events)
    loop.run_forever()

if __name__ == "__main__":
    main()
