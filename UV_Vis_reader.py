import numpy as np
import scipy
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.patches as patches
from PIL import Image
import os
import pandas as pd


def rect_add(region_limits, col):
    x_diff = abs(region_limits[0] - region_limits[1])
    y_diff = abs(region_limits[2] - region_limits[3])
    rect = patches.Rectangle((region_limits[0], region_limits[2]),
                             x_diff, y_diff, linewidth=1, edgecolor=col, facecolor='none')
    return rect


def get_t_adj(t_unit):
    if t_unit == 's':
        t_adj = 1
    elif t_unit == 'min':
        t_adj = 60
    elif t_unit == 'h':
        t_adj = 3600
    return t_adj


def get_date_taken(path):
    return Image.open(path)._getexif()[36867]


def get_date_modified(path):
    return os.path.getmtime(path)


def get_files_time(dir):
    files = os.listdir(dir)
    total = np.empty((len(files), 2), dtype=object)
    for i in range(len(files)):
        with open(os.path.join(dir, files[i])) as current_file:
            df = pd.read_csv(current_file, sep=" ", header=None)
            total[i, 0] = current_file.name
            total[i, 1] = get_date_modified(current_file.name)
    total[:, 1] -= min(total[:, 1])
    df_res = pd.DataFrame(total, columns=["File", "Time"]).sort_values('Time')
    return df_res


def plot_spec(dir, x_range=None, start=0, inc=None, max_num_spec=9, t_adj=1, y_adj_num_poi=10):
    df_file_time = get_files_time(dir)
    files, times = np.hsplit(np.array(df_file_time, dtype=object), 2)
    fig = Figure(figsize=(4, 4), dpi=100)
    ax = fig.add_subplot()
    # ax.rcParams.update({'font.size': 10})
    ax.set_xlabel("Wavelength / nm")
    ax.set_ylabel("Absorbance")
    std_colours = plt.rcParams['axes.prop_cycle'].by_key()['color']
    # min_x, max_x, min_y, max_y = [], [], [], []
    if inc is None: inc = int((len(files) - start) / max_num_spec)
    if len(files) < start + inc * max_num_spec:
        end_spec = int(len(files) / inc) * inc
        max_num_spec = int((len(files) - start) / inc)
    else:
        end_spec = start + inc * max_num_spec
    req_files = [i for i in np.linspace(start, end_spec, max_num_spec + 1, dtype=int) if i < len(files)]
    for i in range(len(req_files)):
        df = pd.read_csv(*files[req_files[i]], sep=" ", header=None)
        x = df.iloc[:, 0].values
        y = df.iloc[:, 1].values
        y_adj = y - np.mean(y[:y_adj_num_poi])
        # min_x, max_x = min(min_x, min(x)), max(max_x, max(x))
        # min_y, max_y = min(min_y, min(y)), max(max_y, max(y))
        ax.plot(x, y_adj, color=std_colours[i], label=round(float(times[req_files[i]] / t_adj), 1))
    if x_range is not None: ax.set_xlim([x_range[0], x_range[1]])
    # ax.set_xlim([min_x, max_x])
    # ax.set_ylim([min_y, max_y])
    ax.legend(prop={'size': 10}, frameon=False)
    # fig.show()
    return fig


def plot_integral(arr, t_unit='s', t_adj=1):
    fig = Figure(figsize=(4, 4), dpi=100)
    ax = fig.add_subplot()
    # ax.rcParams.update({'font.size': 10})
    ax.set_xlabel("Time / " + t_unit)
    ax.set_ylabel("Intensity")
    std_colours = plt.rcParams['axes.prop_cycle'].by_key()['color']
    x = arr[:, 1] / t_adj
    min_y, max_y = min(arr[:, 2]), max(arr[:, 2])
    for i in range(2, arr.shape[1]):
        y = arr[:, i]
        min_y, max_y = min(min_y, min(y)), max(max_y, max(y))
        ax.plot(x, y, color=std_colours[i])
    ax.set_xlim([min(x), max(x)])
    ax.set_ylim([min_y, max_y])
    # fig.show()
    return fig


def integral_calc(dir, region_limits, t_adj=1, y_adj_num_poi=10):
    df_file_time = get_files_time(dir)
    files, times = np.hsplit(np.array(df_file_time, dtype=object), 2)
    total = np.empty((len(files), len(region_limits) + 2), dtype=object)
    total[:, :2] = np.array(df_file_time, dtype=object)
    for i in range(len(files)):
        df = pd.read_csv(*files[i], sep=" ", header=None)
        x = df.iloc[:, 0].values
        y = df.iloc[:, 1].values
        y_adj = y - np.mean(y[:y_adj_num_poi])
        for j in range(len(region_limits)):
            index = np.where(np.logical_and(x >= region_limits[j][0], x <= region_limits[j][1]))
            x_sect = x[index]
            y_sect = y_adj[index]
            area_sect = scipy.integrate.trapezoid(y_sect, x_sect)
            total[i, j + 2] = area_sect
    total[:, 1] -= min(total[:, 1])
    total[:, 1] = total[:, 1] / t_adj
    return total


def spec_export(arr, region_limits, exportpath):
    area_head = [str(region_limits[i][0]) + '-' + str(region_limits[i][1]) for i in range(len(region_limits))]
    df = pd.DataFrame(arr, columns=["File", "Time / s", *area_head])
    writer = pd.ExcelWriter(exportpath, engine='openpyxl')
    df.to_excel(writer, 'Sheet1', index=False)
    writer.save()


if __name__ == "__main__":
    dir = r'C:\Users\Peter\Documents\Postdoctorate\Work\CAKE\Case studies\UV-Vis Enzyme Catalysis\UV-Vis\21040701_Run'  # enter file dir
    show_first_spec = "n"  # enter "y" or "yes" if you want to see first image, to aid region limit selection
    region_limits = [(330, 350), (350, 370)]  # enter primary (x1, x2, y1, y2) area for pixel abstraction
    exportpath = r'C:\Users\Peter\Documents\Postdoctorate\Work\CAKE\Case studies\UV-Vis Enzyme Catalysis\UV-Vis\21040701_330-3502.xlsx'  # enter Excel path for export

    fig = plot_spec(dir)
    # arr_res = integral_calc(dir, region_limits)
    # fig = plot_integral(arr_res)
    # spec_export(arr_res, region_limits, exportpath)
