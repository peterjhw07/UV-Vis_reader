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


def plot_temporal(df):
    fig = Figure(figsize=(4, 4), dpi=100)
    ax = fig.add_subplot()
    # ax.rcParams.update({'font.size': 10})
    ax.set_xlabel(df.columns[1])
    ax.set_ylabel("Intensity")
    std_colours = plt.rcParams['axes.prop_cycle'].by_key()['color']
    x = df.iloc[:, 1]
    min_y, max_y = min(df.iloc[:, 2]), max(df.iloc[:, 2])
    for i in range(2, df.shape[1]):
        y = df.iloc[:, i]
        min_y, max_y = min(min_y, min(y)), max(max_y, max(y))
        ax.plot(x, y, color=std_colours[i], label=df.columns[i])
    ax.set_xlim([min(x), max(x)])
    ax.set_ylim([min_y, max_y])
    if df.shape[1] > 3:
        ax.legend(frameon=False)
    # fig.show()
    return fig


def get_temporal(dir, max_wavelengths=[], region_limits=[], t_adj=1, t_unit='time_unit', y_adj_num_poi=10):
    num_max_wavelengths = len(max_wavelengths)
    df_file_time = get_files_time(dir)
    files, times = np.hsplit(np.array(df_file_time, dtype=object), 2)
    total = np.empty((len(files), num_max_wavelengths + len(region_limits) + 2), dtype=object)
    total[:, :2] = np.array(df_file_time, dtype=object)
    for i in range(len(files)):
        df = pd.read_csv(*files[i], sep=" ", header=None)
        x = df.iloc[:, 0].values
        y = df.iloc[:, 1].values
        y_adj = y - np.mean(y[:y_adj_num_poi])
        for j in range(num_max_wavelengths):
            index = np.argmin(np.abs(x - max_wavelengths[j]))
            total[i, j + 2] = y_adj[index]
        for k in range(len(region_limits)):
            index = np.where(np.logical_and(x >= region_limits[k][0], x <= region_limits[k][1]))
            x_sect = x[index]
            y_sect = y_adj[index]
            area_sect = scipy.integrate.trapezoid(y_sect, x_sect)
            total[i, k + num_max_wavelengths + 2] = area_sect
    total[:, 1] -= min(total[:, 1])
    total[:, 1] = total[:, 1] / t_adj
    area_head = [str(region_limits[i][0]) + '-' + str(region_limits[i][1]) for i in range(len(region_limits))]
    df = pd.DataFrame(total, columns=["File", 'Time / ' + t_unit, *max_wavelengths, *area_head])
    return df


def spec_export(df, exportpath):
    writer = pd.ExcelWriter(exportpath, engine='openpyxl')
    df.to_excel(writer, 'Sheet1', index=False)
    writer.save()


if __name__ == "__main__":
    dir = r'C:\Users\Peter\Documents\Postdoctorate_McIndoe\Work\CAKE\Case studies\UV-Vis Enzyme Catalysis\UV-Vis\21040702_Run'  # enter file dir
    show_first_spec = "n"  # enter "y" or "yes" if you want to see first image, to aid region limit selection
    max_wavelengths = [340, 360]
    region_limits = [(330, 350), (350, 370)]  # enter primary (x1, x2, y1, y2) area for pixel abstraction
    exportpath = r'C:\Users\Peter\Documents\Postdoctorate_McIndoe\Work\CAKE\Case studies\UV-Vis Enzyme Catalysis\UV-Vis\21040702_330-350_2.xlsx'  # enter Excel path for export

    fig = plot_spec(dir)
    df = get_temporal(dir, max_wavelengths=max_wavelengths, region_limits=region_limits)
    fig = plot_temporal(df)
    spec_export(df, exportpath)
