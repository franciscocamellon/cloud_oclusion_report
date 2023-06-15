# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CloudOclusionReportDialog
                                 A QGIS plugin
 Cloud Oclusion Report
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-06-12
        git sha              : $Format:%H$
        copyright            : (C) 2023 by CloudOclusionReport
        email                : CloudOclusionReport@email.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import html
import os
from datetime import datetime

import jinja2
from jinja2 import Environment, PackageLoader, select_autoescape
import pdfkit
from qgis.PyQt import QtWidgets
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QDateTime
from qgis.core import Qgis, QgsProject, QgsMapLayerProxyModel

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'cloud_oclusion_report_dialog_base.ui'))


class CloudOclusionReportDialog(QtWidgets.QDialog, FORM_CLASS):

    def __init__(self, parent=None):
        """Constructor."""
        super(CloudOclusionReportDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.connect_layer_to_field_combo_box()
        self.report_date_de.setDateTime(QDateTime.currentDateTime())
        self.evaluate_end_date_de.setDateTime(QDateTime.currentDateTime())
        self.evaluation_layer_cb.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.evaluate_bt.clicked.connect(self.get_occlusion_result)
        self.report_bt.clicked.connect(self.export_to_pdf)
        self.evaluation_layer_cb.layerChanged.connect(self.connect_layer_to_field_combo_box)

    def connect_layer_to_field_combo_box(self):
        current_layer = self.evaluation_layer_cb.currentLayer()
        self.evaluation_field_cb.setLayer(current_layer)
        # fields_list = [field.name() for field in current_layer.fields()]
        # self.evaluation_field_cb.setFields(fields_list)

    def filter_by_occlusion(self, layer, field):
        nonconforming = []
        conforming = []
        analysis_dict = {}

        for feature in layer.getFeatures():
            texto_edicao = feature['texto_edicao']
            area_oclusao = feature[field]
            if texto_edicao in analysis_dict:
                analysis_dict[texto_edicao].append(area_oclusao)
            else:
                analysis_dict[texto_edicao] = [area_oclusao]
        print(self.occlusion_param_sd.value())
        for key in analysis_dict:
            if max(analysis_dict[key]) >= self.occlusion_param_sd.value():
                nonconforming.append(key)
            else:
                conforming.append(key)

        return conforming, nonconforming

    def get_occlusion_result(self):
        conforming, nonconforming = self.filter_by_occlusion(self.evaluation_layer_cb.currentLayer(),
                                                             self.evaluation_field_cb.currentField()
                                                             )
        block_text = self.block_cb.currentText()

        if block_text in nonconforming:
            analysis_answer = 'Foram identificadas nuvens ou oclusões com área maior ou igual a 0,2 km².'
            conformity = 'Não Conforme'
        else:
            analysis_answer = 'Não foram identificadas nuvens ou oclusões com área maior ou igual a 0,2 km².'
            conformity = 'Conforme'
        print(analysis_answer, conformity)
        return analysis_answer, conformity

    def get_input_data(self):
        analysis_answer, conformity = self.get_occlusion_result()

        input_data = [
            self.om_cb.currentText(),
            self.report_number_sp.text(),
            self.block_cb.currentText(),
            self.work_period_month_cb.currentText(),
            self.work_period_year_cb.currentText(),
            self.evaluate_end_date_de.text(),
            conformity,
            analysis_answer,
            '{} {}'.format(self.evaluator_grad_cb.currentText(), self.evaluator_name_le.text()),
            '{} {}'.format(self.manager_pst_cb.currentText(), self.manager_name_le.text()),
            self.report_date_de.text()
        ]

        print(input_data)
        return input_data

    def string_to_html_text(self, string_data):

        return html.escape(string_data, quote=False).encode("utf-8", "xmlcharrefreplace").decode("utf-8")

    def get_cgeo_name_and_location(self, string):
        cgeo_map = {
            "1º CGEO": ("1º CENTRO DE GEOINFORMAÇÃO", "Porto Alegre - RS,"),
            "2º CGEO": ("2º CENTRO DE GEOINFORMAÇÃO", "Brasília - DF,"),
            "3º CGEO": ("3º CENTRO DE GEOINFORMAÇÃO", "Olinda - PE,"),
            "4º CGEO": ("4º CENTRO DE GEOINFORMAÇÃO", "Manaus - AM,"),
            "5º CGEO": ("5º CENTRO DE GEOINFORMAÇÃO", "Rio de Janeiro - RJ,")
        }

        cgeo_name, cgeo_location = cgeo_map.get(string, ("error", None))

        return cgeo_name, cgeo_location

    def get_html_data(self):
        evaluate_data = self.get_input_data()
        cgeo_name, cgeo_location = self.get_cgeo_name_and_location(evaluate_data[0])

        context = {'product_type': 'Ortoimagem',
                   'om_name': self.string_to_html_text(cgeo_name),
                   'doc_number': self.string_to_html_text(evaluate_data[1]),
                   'block': self.string_to_html_text(evaluate_data[2]),
                   'work_month': self.string_to_html_text(evaluate_data[3]),
                   'work_year': self.string_to_html_text(evaluate_data[4]),
                   'map_scale': '1:10.000',
                   'src': 'SIRGAS 2000 UTM 24S',
                   'finish_project_date': self.string_to_html_text(evaluate_data[5]),
                   'evaluation_result': self.string_to_html_text(evaluate_data[7]),
                   'project_name': self.string_to_html_text('Perícia PI/CE'),
                   'conformity': self.string_to_html_text(evaluate_data[6]),
                   'responsavel_tecnico': self.string_to_html_text(evaluate_data[9]),
                   'avaliador': self.string_to_html_text(evaluate_data[8]),
                   'local_and_time': self.string_to_html_text(cgeo_location) + self.string_to_html_text(evaluate_data[10])
                   }
        return context

    def export_to_pdf(self):

        # Aqui vamos passar como um dicionário as variáveis que são usadas no HTML
        project_name = self.string_to_html_text('Perícia PI/CE')

        context = self.get_html_data()

        template_env = jinja2.Environment(loader=PackageLoader("cloud_oclusion_report", 'templates'),
                                          autoescape=select_autoescape())

        template = template_env.get_template("basic-template.html")  # função que chama o modelo HTML pronto
        output_text = template.render(context)

        today_date = datetime.today().strftime("%d %b %Y")
        docNumberToFileName = context['doc_number'].split('/')
        fileName = 'Relatorio Tecnico Nr ' + docNumberToFileName[0] + ' - ' + str(today_date) + '.pdf'

        css_file = os.path.join(os.path.dirname(__file__), 'templates', 'my-style.css')
        config = pdfkit.configuration(wkhtmltopdf="C:/Program Files (x86)/wkhtmltopdf/bin/wkhtmltopdf.exe")
        pdfkit.from_string(output_text, fileName, configuration=config, css=css_file)
        self.pdf_destination_fw
        print('PDF Gerado com sucesso')

    def convert_text_to_pdf(self, output_text, destination_path, configuration=None, css=None):
        try:
            file_name = os.path.join(destination_path, "output.pdf")
            pdfkit.from_string(output_text, file_name, configuration=configuration, css=css)
            print(f"PDF created successfully at {file_name}.")
        except Exception as e:
            print(f"Error creating PDF: {str(e)}")
    def show_success_message_bar(self, iface, message):
        iface.messageBar().pushMessage(message, level=Qgis.Success, duration=5)
