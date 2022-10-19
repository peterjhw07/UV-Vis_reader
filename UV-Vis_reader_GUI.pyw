import PySimpleGUI as sg
import os.path
import textwrap
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import UV_Vis_reader

def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both')
    return figure_canvas_agg


fig_canvas_agg = []
folder = []
t_unit = 's'
t_adj = 1
x_range = None
start = 0
inc = None
region_limits = []

sg.theme('LightBrown2')

file_list_column = [
    [sg.Text("UV-Vis Spectra Processor", font='Any 18')],
    #[sg.Text("This program shows multiple UV-Vis spectra on a single figure, integrate a peak in multiple UV-Vis spectra and graph these results")],
    [
        sg.Text("UV-Vis files folder"),
        sg.Input(size=(25, 1), enable_events=True, key="-FOLDER-"),
        sg.FolderBrowse()
    ],
    [sg.Listbox(values=[], enable_events=True, size=(40, 10), key="-FILE LIST-")],
    [
        sg.Text("Time unit"),
        sg.Combo(["s", "min", "h"], default_value="s", enable_events=True, key="-t_unit-")
    ],
    [sg.Text("Show absorption spectra", font=("Arial", 12, ' underline'))],
    [
        sg.Text("First spectrum"),
        sg.InputText(size=(5, 1), key="-FS-"),
        sg.Text("Spectra increment"),
        sg.InputText(size=(5, 1), key="-SI-"),
    ],
    [
        sg.Text("Lower x bound"),
        sg.InputText(size=(5, 1), key="-LB1-"),
        sg.Text("Upper x bound"),
        sg.InputText(size=(5, 1), key="-UB1-"),
    ],
    [sg.Button('Submit/Update', key="-SUBMIT1-")],
    [sg.Text("Calculate integrals and export", font=("Arial", 12, ' underline'))],
    [
        sg.Text("Lower range limit"),
        sg.InputText(size=(5, 1), key="-LB2-"),
        sg.Text("Upper range limit"),
        sg.InputText(size=(5, 1), key="-UB2-"),
    ],
    [
        sg.Text("Export path"),
        sg.Input(size=(25, 1), enable_events=True, key="-FILE-"),
        sg.FileBrowse()
    ],
    [sg.Button('Submit/Update', key="-SUBMIT2-")],
]

image_viewer_column = [
    [sg.Text('Plot', font=("Arial", 12, ' underline'))],
    [sg.Frame("Frame", [[sg.Canvas(key='-CANVAS-', expand_x=True, expand_y=True)]], size=(450, 450))]
]

layout = [
    [
        sg.Column(file_list_column),
        sg.VSeperator(),
        sg.Column(image_viewer_column),
    ]
]

window = sg.Window("UV-Vis Spectra Processor", layout, resizable=True, finalize=True)

while True:
    event, values = window.read()
    if event == "Exit" or event == sg.WIN_CLOSED:
        break
    # Folder name was filled in, make a list of files in the folder
    if event == "-FOLDER-":
        folder = values["-FOLDER-"]
        try:
            # Get list of files in folder
            file_list = os.listdir(folder)
        except:
            file_list = []

        fnames = [
            f
            for f in file_list
            if os.path.isfile(os.path.join(folder, f))
            and f.lower().endswith((".txt"))
        ]
        window["-FILE LIST-"].update(fnames)
    elif event == "-FILE-":
        exportpath = values["-FILE-"]

    elif event == "-t_unit-":
        t_unit = values["-t_unit-"]
        t_adj = UV_Vis_reader.get_t_adj(t_unit)

    elif event == "-SUBMIT1-":
        try:
            if values["-FS-"] != '': start = int(values["-FS-"])
            if values["-SI-"] != '': inc = int(values["-SI-"])
            if values["-LB1-"] != '' or values["-LB1-"] != '': x_range = tuple([float(values["-LB1-"]), float(values["-UB1-"])])
            if fig_canvas_agg: fig_canvas_agg.get_tk_widget().forget()
            fig = UV_Vis_reader.plot_spec(folder, x_range=x_range, start=start, inc=inc, t_adj=t_adj)
            fig_canvas_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
        except:
            if not folder:
                sg.Popup('Select data folder')
            else:
                sg.Popup('Error detected. Please refer to operating manual')

    elif event == "-SUBMIT2-":
        try:
            region_limits = [tuple([float(values["-LB2-"]), float(values["-UB2-"])])]
            arr_res = UV_Vis_reader.integral_calc(folder, region_limits, t_adj=t_adj)
            UV_Vis_reader.spec_export(arr_res, region_limits, exportpath)
            if fig_canvas_agg: fig_canvas_agg.get_tk_widget().forget()
            fig = UV_Vis_reader.plot_integral(arr_res, t_unit=t_unit)
            fig_canvas_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
        except:
            try:
                region_limits = [tuple([float(values["-LB2-"]), float(values["-UB2-"])])]
                try:
                    arr_res = UV_Vis_reader.integral_calc(folder, region_limits, t_adj=t_adj)
                    if fig_canvas_agg: fig_canvas_agg.get_tk_widget().forget()
                    fig = UV_Vis_reader.plot_integral(arr_res, t_unit=t_unit)
                    fig_canvas_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
                except:
                    if not folder:
                        sg.Popup('Select data folder')
                    else:
                        sg.Popup('Error detected - please refer to operating manual')
            except:
                if not folder:
                    sg.Popup('Select data folder')
                elif not region_limits:
                    sg.Popup('Input lower and upper range limit')
                else:
                    sg.Popup('Error detected - please refer to operating manual')

window.close()