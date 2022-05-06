"""XRD plotter"""
import os
import re
import pickle
import numpy as np
import time

from matplotlib import pyplot as plt
import pandas as pd

import specio
import brml_converter

plt.ion()

def plot_xrd(xrd_data,pdflist=[]):
    """method to plot xrd data and add PDF Cards

    Parameters:
    -----------
    xrd_data = specio.Spectrum
    pdf_list = list of strings with PDF Card short Name
    """
    fig, ax = plt.subplots()
    ax.plot(xrd_data.wavelength,xrd_data.amplitudes, label = xrd_data.meta['SampleName'])
    if len(pdflist)!=0:
        pdfs_plot_data = add_pdfs(pdflist, xrd_data, ax)
        for pdf in pdfs_plot_data:
            pdf_card, pdf_twotheta, pdf_counts, pdf_color = pdf
            ax.bar(pdf_twotheta, pdf_counts, 0.2, color=pdf_color, label=pdf_card)
    plt.xlim((xrd_data.wavelength.min(),xrd_data.wavelength.max()))
    plt.xlabel('2'+r'$\theta$'+' [°]')
    plt.ylabel('Counts [a.u.]')
    plt.title(xrd_data.meta['SampleName'])
    ax.legend(frameon=False)
    
    return fig, ax
    


def add_pdfs(pdflist,xrd_data,ax):
    color_list = ["red", 'green', 'blue', "purple"]
    i = 0
    pdfs_plot_data = []
    pdf_pattern = re.compile('[\W_]+')
    pdf_path = ".//pdf_dic.p"
    pdf_names_path = ".//pdf_names.p"
    pdf_dic = pickle.load(open(pdf_path,'rb'))
    pdf_names = pickle.load(open(pdf_names_path,'rb'))
    for pdf in pdflist:
        while True:
            try:
                pdf_card_number = pdf_names.get(pdf_pattern.sub("",pdf.lower()))
                break
            except KeyError:
                break
        pdf_data = [pdf_card_number]
        pdf_df = pdf_dic.get(pdf_card_number)
        pdf_arr = pdf_df.to_numpy().astype(float)
        twotheta, counts = np.hsplit(pdf_arr,2)
        twotheta = np.resize(twotheta,(twotheta.shape[0],))
        pdf_data.append(twotheta)
        counts = np.resize(counts,(counts.shape[0],))
        counts = (counts/100)*float(xrd_data.amplitudes.max())*0.8
        pdf_data.append(counts)
        pdf_data.append(color_list[i])
        i = i+1
        pdfs_plot_data.append(pdf_data)
    return pdfs_plot_data


def to_csv(file_path, export_dir=None):
    xrd_data = specio.specread(file_path)
    df = pd.DataFrame(data=[xrd_data.wavelength, xrd_data.amplitudes],
                      index=['2theta', 'counts']).transpose()
    if export_dir is None:
        export_dir = os.path.dirname(file_path)
    df.to_csv(os.path.join(export_dir, xrd_data.meta['SampleName']+'.csv'), index=False)


def convert_plot_export(file_path, pdf_list=[],):
    xrd_data = specio.specread(file_path)
    fig, ax = plot_xrd(xrd_data, pdf_list)
    return fig, xrd_data
    
    
