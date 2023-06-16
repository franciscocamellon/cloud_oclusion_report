# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CloudOcclusionReportDialog
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

import os

from qgis.PyQt import QtWidgets
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QDateTime
from qgis.core import Qgis, QgsProject, QgsMapLayerProxyModel

from .core.util import get_html_data
from .core.occlusion_analisys import get_occlusion_result
from .core.generate_pdf import convert_text_to_pdf

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'cloud_oclusion_report_dialog_base.ui'))


class CloudOcclusionReportDialog(QtWidgets.QDialog, FORM_CLASS):

    def __init__(self, parent=None):
        """Constructor."""
        super(CloudOcclusionReportDialog, self).__init__(parent)
        self.setupUi(self)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.report_number_sp.setMaximum(1000000)
        self.on_evaluate_layer_changed()
        self.report_date_de.setDateTime(QDateTime.currentDateTime())
        self.evaluate_end_date_de.setDateTime(QDateTime.currentDateTime())
        self.evaluation_layer_cb.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        # self.evaluate_bt.clicked.connect(self.on_evaluate_button_clicked)
        self.report_bt.clicked.connect(self.on_report_button_clicked)
        self.cancel_bt.clicked.connect(self.close)
        self.evaluation_layer_cb.layerChanged.connect(self.on_evaluate_layer_changed)

    def on_evaluate_layer_changed(self):
        self.evaluation_field_cb.setLayer(self.evaluation_layer_cb.currentLayer())

    def on_evaluate_button_clicked(self):
        return get_occlusion_result(self.evaluation_layer_cb.currentLayer(),
                                    self.evaluation_field_cb.currentField(),
                                    self.occlusion_param_sd.value(),
                                    self.block_cb.currentText())

    def get_input_data(self):
        analysis_answer, conformity = get_occlusion_result(self.evaluation_layer_cb.currentLayer(),
                                                           self.evaluation_field_cb.currentField(),
                                                           self.occlusion_param_sd.value(),
                                                           self.block_cb.currentText(),
                                                           self.progress_bar)

        input_data = [
            self.om_cb.currentText(),
            self.report_number_sp.text(),
            self.block_cb.currentText(),
            self.work_period_month_cb.currentText(),
            self.work_period_year_cb.currentText(),
            self.evaluate_end_date_de.text(),
            conformity,
            analysis_answer,
            f'{self.evaluator_name_le.text()} - {self.evaluator_grad_cb.currentText()}',
            f'{self.manager_name_le.text()} - {self.manager_pst_cb.currentText()}',
            self.report_date_de.text(),
            self.project_name_le.text(),
            self.project_product_cb.currentText(),
            self.project_scale_cb.currentText(),
        ]

        return input_data

    def on_report_button_clicked(self):
        context = get_html_data(self.get_input_data())
        convert_text_to_pdf(context, self.report_number_sp.text(),
                            self.pdf_destination_fw.filePath())
