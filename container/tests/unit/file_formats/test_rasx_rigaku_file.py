import json
import os
from pathlib import Path
import pandas as pd
import pytest
from typing import Final
import zipfile

from rdetoolkit.exceptions import StructuredError
from rdetoolkit.rde2util import Meta

from file_formats.rasx_rigaku_schema import MeasurementConditions, RASHeader, String, ScanInformation, GeneralInformation, Axes, Axis
from file_formats.rasx_rigaku_schema import HWConfigurations, Optics, Detector, XrayGenerator, Distances, Categories, Distance, Category
from file_formats.rasx_rigaku_file import FileReader, MetaParser


INPUT_FILE = Path('tests/inputdata/test.rasx')
INPUT_EMPTY_FILE = Path('tests/inputdata/test_empty.rasx')
SINGLE_REGION_NUM: Final[int] = 1
MULTI_REGION_NUM: Final[int] = 2
RDE_CONFIG_YAML: dict = {
    'system': {
        'magic_variable': True,
        'save_thumbnail_image': True,
    },
    'xrd': {
        'filename_mapping_rule': True,
        'manufacturer': 'rigaku',
        'main_image_setting': None,
        'meas_scan_axis_x': None,
        'meas_scan_unit_x': None,
        'meas_scan_axis_y': None,
        'meas_scan_unit_y': None
    }
}


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def input_data():
    return pd.DataFrame({
        0: [1.00, 1.01, 1.02, 1.03, 1.04],
        1: [929, 889, 856, 840, 819],
        2: [1, 1, 1, 1, 1]
    })


@pytest.fixture
def read_data():
    return pd.DataFrame({
        "2Theta-Theta (deg)": [1.00, 1.01, 1.02, 1.03, 1.04],
        "Intensity (counts)": [929, 889, 856, 840, 819],
    })


@pytest.fixture
def read_meta():
    # MEMO: WaveType= 'Ka' -> 'K_alpha'
    return MeasurementConditions(generalinformation=GeneralInformation(Comment='', Operator='nims', PackageName='', PartName='GeneralMeasurement', SampleName='', Type='RAS_RAW', SystemName='MiniFlex', UserGroup='Administrators', Version='1', Memo=''), hwconfigurations=HWConfigurations(categories=Categories(category=[Category(Name='Goniometer', SelectedUnit='Standard'), Category(Name='IncidentCBO', SelectedUnit='No_unit'), Category(Name='ReceivingOptics1', SelectedUnit='No_unit'), Category(Name='ReceivingAttenuator', SelectedUnit='No_unit'), Category(Name='Detector', SelectedUnit='DteX100'), Category(Name='DetectorMonochromator', SelectedUnit='None')]), distances=Distances(distance=[Distance(To='IncidentPrimary', From='XrayGenerator', Unit='mm', Value='90'), Distance(To='IncidentCBO', From='XrayGenerator', Unit='mm', Value='114'), Distance(To='IncidentSlit', From='XrayGenerator', Unit='mm', Value='91.5'), Distance(To='AttachmentStage', From='XrayGenerator', Unit='mm', Value='150'), Distance(To='ReceivingSlitBox1', From='AttachmentStage', Unit='mm', Value='103.4'), Distance(To='ReceivingSlitBox2', From='AttachmentStage', Unit='mm', Value='150'), Distance(To='ReceivingSlitBox2', From='ReceivingSlitBox1', Unit='mm', Value='46.6'), Distance(To='Detector', From='AttachmentStage', Unit='mm', Value='150')]), xraygenerator=XrayGenerator(Type='Hermetic', FocusSize='0.4mm x 8mm', FocusType='Fine', TargetAtomicNumber='29', TargetName='Cu', WaveType='Ka', Current='15', CurrentUnit='mA', Voltage='40', VoltageUnit='kV', WavelengthKbeta='1.392246', WavelengthKalpha1='1.540593', WavelengthKalpha2='1.544414'), detector=Detector(PHAUnit='div', PHABase='30', PHAWindow='20', PixelSize='0.1'), optics=Optics(Name='', Attribute='')), axes=Axes(axis=[Axis(Name='TwoThetaTheta', Unit='deg', Offset='0', Position='12.0000', State='Scan', Resolution='0.0025'), Axis(Name='ISS', Unit='', Offset='0', Position='Soller_slit_2.5deg', State='Fixed', Resolution=''), Axis(Name='IS', Unit='', Offset='0', Position='1.25deg', State='Fixed', Resolution=''), Axis(Name='IS', Unit='', Offset='0', Position='1.25deg', State='Fixed', Resolution=''), Axis(Name='IS', Unit='', Offset='0', Position='1.25deg', State='Fixed', Resolution=''), Axis(Name='LLS', Unit='', Offset='0', Position='10mm', State='Fixed', Resolution=''), Axis(Name='LLS', Unit='', Offset='0', Position='10mm', State='Fixed', Resolution=''), Axis(Name='LLS', Unit='', Offset='0', Position='10mm', State='Fixed', Resolution=''), Axis(Name='Filter1', Unit='', Offset='0', Position='None', State='Fixed', Resolution=''), Axis(Name='Beta', Unit='deg', Offset='0', Position='', State='Rotation', Resolution='0.9'), Axis(Name='Changer', Unit='', Offset='0', Position='1', State='Fixed', Resolution='1'), Axis(Name='RS1', Unit='', Offset='0', Position='Open', State='Fixed', Resolution=''), Axis(Name='RS1', Unit='', Offset='0', Position='Open', State='Fixed', Resolution=''), Axis(Name='RS1', Unit='', Offset='0', Position='Open', State='Fixed', Resolution=''), Axis(Name='Filter1', Unit='', Offset='0', Position='K_beta_x1', State='Fixed', Resolution=''), Axis(Name='RSS', Unit='', Offset='0', Position='Soller_slit_2.5deg', State='Fixed', Resolution=''), Axis(Name='RS2', Unit='', Offset='0', Position='Open', State='Fixed', Resolution=''), Axis(Name='RS2', Unit='', Offset='0', Position='Open', State='Fixed', Resolution=''), Axis(Name='RS2', Unit='', Offset='0', Position='Open', State='Fixed', Resolution=''), Axis(Name='PHA', Unit='div', Offset='0', Position='30', State='Fixed', Resolution='1'), Axis(Name='RS3', Unit='', Offset='0', Position='Open', State='Fixed', Resolution='0.1'), Axis(Name='Target_TargetTime', Unit='H', Offset='0', Position='', State='Fixed', Resolution='0.01'), Axis(Name='Target_XrayOnTime', Unit='H', Offset='0', Position='', State='Fixed', Resolution='0.010000'), Axis(Name='Target_TMPTime', Unit='H', Offset='0', Position='', State='Fixed', Resolution='0.01'), Axis(Name='Target_RPTime', Unit='H', Offset='0', Position='', State='Fixed', Resolution='0.01'), Axis(Name='Target_FilamentTime', Unit='H', Offset='0', Position='', State='Fixed', Resolution='0.01'), Axis(Name='Target_IG', Unit='mV', Offset='0', Position='', State='Fixed', Resolution='1'), Axis(Name='Target_GP', Unit='V', Offset='0', Position='', State='Fixed', Resolution='1'), Axis(Name='Target_FC', Unit='V', Offset='0', Position='', State='Fixed', Resolution='1'), Axis(Name='HVPS_Bias', Unit='V', Offset='0', Position='', State='Fixed', Resolution='1'), Axis(Name='HVPS_HVPSTime', Unit='H', Offset='0', Position='', State='Fixed', Resolution='0.01'), Axis(Name='HVPS_Type1Time', Unit='H', Offset='0', Position='', State='Fixed', Resolution='0.01'), Axis(Name='HVPS_Type2Time', Unit='H', Offset='0', Position='', State='Fixed', Resolution='0.01'), Axis(Name='HVPS_Type3Time', Unit='H', Offset='0', Position='', State='Fixed', Resolution='0.01'), Axis(Name='CW_IERTime', Unit='H', Offset='0', Position='', State='Fixed', Resolution='0.010000'), Axis(Name='CW_ECTime', Unit='uS/m', Offset='0', Position='', State='Fixed', Resolution='1'), Axis(Name='CW_Flow1', Unit='L/min', Offset='0', Position='', State='Fixed', Resolution='0.100000'), Axis(Name='CW_Temperature1', Unit='degree', Offset='0', Position='', State='Fixed', Resolution='1.000000'), Axis(Name='CW_Pressure1', Unit='MPa', Offset='0', Position='', State='Fixed', Resolution='0.010000'), Axis(Name='CW_PressureIn', Unit='MPa', Offset='0', Position='', State='Fixed', Resolution='0.01'), Axis(Name='CW_PressureOut', Unit='MPa', Offset='0', Position='', State='Fixed', Resolution='0.01'), Axis(Name='CW_Flow2', Unit='L/min', Offset='0', Position='', State='Fixed', Resolution='0.1'), Axis(Name='CW_Temperature2', Unit='C', Offset='0', Position='', State='Fixed', Resolution='1'), Axis(Name='CW_Pressure2', Unit='MPa', Offset='0', Position='', State='Fixed', Resolution='0.01'), Axis(Name='RE_EnclosureTemp', Unit='degree', Offset='0', Position='', State='Fixed', Resolution='1.000000'), Axis(Name='RE_EnclosureHummidity', Unit='percent', Offset='0', Position='', State='Fixed', Resolution='1'), Axis(Name='RE_CabinetTemp', Unit='degree', Offset='0', Position='', State='Fixed', Resolution='1.000000'), Axis(Name='RE_RPTemp', Unit='C', Offset='0', Position='', State='Fixed', Resolution='1'), Axis(Name='RE_ShutterAXrayOnTime', Unit='H', Offset='0', Position='', State='Fixed', Resolution='0.01'), Axis(Name='RE_ShutterATimes', Unit='time', Offset='0', Position='', State='Fixed', Resolution='1'), Axis(Name='RE_ShutterAOpenCloseTime', Unit='msec', Offset='0', Position='', State='Fixed', Resolution='1'), Axis(Name='RE_ShutterACloseOpenTime', Unit='msec', Offset='0', Position='', State='Fixed', Resolution='1'), Axis(Name='RE_ShutterBXrayOnTime', Unit='H', Offset='0', Position='', State='Fixed', Resolution='0.01'), Axis(Name='RE_ShutterBTimes', Unit='times', Offset='0', Position='', State='Fixed', Resolution='1.000000'), Axis(Name='RE_ShutterBOpenCloseTime', Unit='msec', Offset='0', Position='', State='Fixed', Resolution='1.000000'), Axis(Name='RE_ShutterBCloseOpenTime', Unit='msec', Offset='0', Position='', State='Fixed', Resolution='1.000000'), Axis(Name='RE_XrayWarningRamp', Unit='-', Offset='0', Position='', State='Fixed', Resolution='-'), Axis(Name='RE_ShutterAInstallation', Unit='-', Offset='0', Position='', State='Fixed', Resolution='-'), Axis(Name='RE_ShutterARamp', Unit='-', Offset='0', Position='', State='Fixed', Resolution='-'), Axis(Name='RE_ShutterBInstallation', Unit='', Offset='0', Position='', State='Fixed', Resolution='1.000000'), Axis(Name='RE_ShutterBRamp', Unit='-', Offset='0', Position='', State='Fixed', Resolution='-'), Axis(Name='RE_ExtShutterCLS', Unit='-', Offset='0', Position='', State='Fixed', Resolution='-'), Axis(Name='RE_ExtXrayOFF', Unit='-', Offset='0', Position='', State='Fixed', Resolution='-'), Axis(Name='RE_ExtSafetyCircuit', Unit='', Offset='0', Position='', State='Fixed', Resolution='1.000000'), Axis(Name='Version_CPU', Unit='', Offset='0', Position='', State='Fixed', Resolution='1.000000'), Axis(Name='Version_RS1', Unit='', Offset='0', Position='', State='Fixed', Resolution='1.000000'), Axis(Name='Version_RS2', Unit='', Offset='0', Position='', State='Fixed', Resolution='1.000000'), Axis(Name='Version_HV', Unit='', Offset='0', Position='', State='Fixed', Resolution='1.000000'), Axis(Name='Version_CW', Unit='', Offset='0', Position='', State='Fixed', Resolution='1.000000'), Axis(Name='Version_RT', Unit='', Offset='0', Position='', State='Fixed', Resolution='1.000000'), Axis(Name='IncidentPrimary', Unit='', Offset='0', Position='No_unit', State='', Resolution=''), Axis(Name='IncidentOptics', Unit='', Offset='0', Position='Manual', State='', Resolution=''), Axis(Name='ReceivingOptics1', Unit='', Offset='0', Position='No_unit', State='', Resolution=''), Axis(Name='DetectorMonochromator', Unit='', Offset='0', Position='None', State='', Resolution='')]), scaninformation=ScanInformation(AxisName='2Theta-Theta', Mode='CONTINUOUS', Start='1.0000', Stop='100.0000', Step='0.0100', Speed='3.0000', Resolution='0.0025', SpeedUnit='deg/min', PositionUnit='deg', IntensityUnit='counts', StartTime='2022-11-07T01:00:24Z', EndTime='2022-11-07T01:35:20Z', AttenuatorAutoMode=False, UnequalySpaced=False, DataCount='9901', DscStartTime='0001-01-01T00:00:00', DscEndTime='0001-01-01T00:00:00'), rasheader=RASHeader(Pair=[String(string='*DISP_LINE_COLOR'), String(string='*FILE_MD5'), String(string='*HW_ATTACHMENT_NAME_INTERNAL'), String(string='*HW_COUNTER_MONOCHRO_ID'), String(string='*HW_COUNTER_MONOCHRO_NAME'), String(string='*HW_COUNTER_MONOCHRO_NAME_INTERNAL'), String(string='*HW_COUNTER_NAME_INTERNAL'), String(string='*HW_COUNTER_NAME-0'), String(string='*HW_COUNTER_NAME-1'), String(string='*HW_COUNTER_SELECT_NAME'), String(string='*HW_GONIOMETER_NAME'), String(string='*HW_GONIOMETER_NAME_INTERNAL'), String(string='*HW_I_CBO_ID'), String(string='*HW_I_CBO_NAME'), String(string='*HW_I_CBO_NAME_INTERNAL'), String(string='*HW_I_MONOCHRO_NAME_INTERNAL'), String(string='*HW_I_PRIMARY_NAME_INTERNAL'), String(string='*HW_I_SLIT_NAME_INTERNAL'), String(string='*HW_R_ATTENUATER_ID'), String(string='*HW_R_ATTENUATER_NAME'), String(string='*HW_R_ATTENUATOR_NAME_INTERNAL'), String(string='*HW_R_ROD_ID'), String(string='*HW_R_ROD_NAME'), String(string='*HW_R_ROD_NAME_INTERNAL'), String(string='*HW_R_RPS_NAME_INTERNAL'), String(string='*HW_R_RS_NAME_INTERNAL'), String(string='*HW_R_SS_NAME_INTERNAL'), String(string='*HW_SAMPLE_HOLDER_NAME_INTERNAL'), String(string='*HW_SAMPLE_NAME'), String(string='*HW_SAMPLE_NAME_INTERNAL'), String(string='*HW_SAMPLE_PLATE_NAME'), String(string='*HW_SAMPLE_PLATE_NAME_INTERNAL'), String(string='*HW_SAMPLE_SPACER_NAME'), String(string='*HW_SAMPLE_SPACER_NAME_INTERNAL'), String(string='*HW_USERINFO_CATALOG_NO'), String(string='*HW_USERINFO_INSTRUMENT_ID'), String(string='*HW_USERINFO_INSTRUMENT_NAME'), String(string='*HW_USERINFO_INSTRUMENT_NO'), String(string='*HW_USERINFO_MODEL'), String(string='*HW_USERINFO_ORDER_NO'), String(string='*HW_USERINFO_SERIAL_NO'), String(string='*HW_USERINFO_VERIFY_INSTRUMENT_ID'), String(string='*HW_VER_RCD_COUNTER_UNIT'), String(string='*HW_VER_RCD_CPU'), String(string='*HW_VER_RCD_FPGA'), String(string='*HW_VER_RCD_GONIO_UNIT'), String(string='*HW_VER_RCD_INCIDENT_UNIT'), String(string='*HW_VER_RCD_RECEIVING_UNIT'), String(string='*HW_VER_RCD_TYPE'), String(string='*HW_VER_XGC_CPU'), String(string='*HW_VER_XGC_CW'), String(string='*HW_VER_XGC_HV'), String(string='*HW_VER_XGC_RS1'), String(string='*HW_VER_XGC_RS2'), String(string='*HW_VER_XGC_RT'), String(string='*HW_VER_XGC_TYPE'), String(string='*HW_XG_WAVE_LENGTH_UNIT'), String(string='*MEAS_COND_AXIS_NAME-0'), String(string='*MEAS_COND_AXIS_NAME-1'), String(string='*MEAS_COND_COUNTER_CENTER_X'), String(string='*MEAS_COND_COUNTER_CENTER_Y'), String(string='*MEAS_COND_COUNTER_COUNTMODE'), String(string='*MEAS_COND_COUNTER_DEADTIMECORRECTION'), String(string='*MEAS_COND_COUNTER_DISTANCE'), String(string='*MEAS_COND_COUNTER_ENERGYMODE'), String(string='*MEAS_COND_COUNTER_PITCH_X'), String(string='*MEAS_COND_COUNTER_PITCH_Y'), String(string='*MEAS_COND_COUNTER_PITCHUNIT'), String(string='*MEAS_COND_COUNTER_VALIDWIDTH_X'), String(string='*MEAS_COND_COUNTER_VALIDWIDTH_Y'), String(string='*MEAS_SCAN_AXIS_X'), String(string='*MEAS_SCAN_MODE_INTERNAL')]), sampleinformation='')


@pytest.fixture
def metadata_def(tmp_path):
    """metadata-def.json"""
    metadata_def = {
        "rasx.specimen": {
            "name": {
                "ja": "試料",
                "en": "Specimen"
            },
            "schema": {
                "type": "string"
            },
            "order": 1,
            "mode": "rasx形式",
            "originalName": "SampleName",
            "variable": 1
        },
        "rasx.comment": {
            "name": {
                "ja": "コメント",
                "en": "Comment"
            },
            "schema": {
                "type": "string"
            },
            "order": 2,
            "mode": "rasx形式",
            "originalName": "Comment",
            "variable": 1
        },
        "rasx.selected_detector_name": {
            "name": {
                "ja": "使用検出器名称",
                "en": "Selected Detector Name"
            },
            "schema": {
                "type": "string"
            },
            "order": 3,
            "mode": "rasx形式",
            "originalName": "Detector",
            "variable": 1
        },
        "rasx.scan_axis": {
            "name": {
                "ja": "スキャン軸",
                "en": "Scan Axis"
            },
            "schema": {
                "type": "string"
            },
            "order": 4,
            "mode": "rasx形式",
            "originalName": "AxisName",
            "variable": 1
        },
        "rasx.scan_mode": {
            "name": {
                "ja": "スキャンモード",
                "en": "Scan Mode"
            },
            "schema": {
                "type": "string"
            },
            "order": 5,
            "mode": "rasx形式",
            "originalName": "Mode",
            "variable": 1
        },
        "rasx.x-ray_tube_current": {
            "name": {
                "ja": "X線管電流",
                "en": "X-ray Tube Current"
            },
            "schema": {
                "type": "number"
            },
            "order": 6,
            "unit": "$CurrentUnit",
            "mode": "rasx形式",
            "originalName": "Current",
            "variable": 1
        },
        "rasx.x-ray_tube_voltage": {
            "name": {
                "ja": "X線管電圧",
                "en": "X-ray Tube Voltage"
            },
            "schema": {
                "type": "number"
            },
            "order": 7,
            "unit": "$VoltageUnit",
            "mode": "rasx形式",
            "originalName": "Voltage",
            "variable": 1
        },
        "rasx.scan_starting_position": {
            "name": {
                "ja": "スキャン開始位置",
                "en": "Scan Starting Position"
            },
            "schema": {
                "type": "number"
            },
            "order": 8,
            "unit": "$PositionUnit",
            "mode": "rasx形式",
            "originalName": "Start",
            "variable": 1
        },
        "rasx.scan_ending_position": {
            "name": {
                "ja": "スキャン終了位置",
                "en": "Scan Ending Position"
            },
            "schema": {
                "type": "number"
            },
            "order": 9,
            "unit": "$PositionUnit",
            "mode": "rasx形式",
            "originalName": "Stop",
            "variable": 1
        },
        "rasx.scan_step_size": {
            "name": {
                "ja": "スキャンステップサイズ",
                "en": "Scan Step Size"
            },
            "schema": {
                "type": "number"
            },
            "order": 10,
            "unit": "$PositionUnit",
            "mode": "rasx形式",
            "originalName": "Step",
            "variable": 1
        },
        "rasx.scan_speed": {
            "name": {
                "ja": "スキャンスピード",
                "en": "Scan Speed"
            },
            "schema": {
                "type": "number"
            },
            "order": 11,
            "unit": "$SpeedUnit",
            "mode": "rasx形式",
            "originalName": "Speed",
            "variable": 1
        },
        "rasx.scan_starting_date_time": {
            "name": {
                "ja": "スキャン開始時刻",
                "en": "Scan Starting Date Time"
            },
            "schema": {
                "type": "string"
            },
            "order": 12,
            "mode": "rasx形式",
            "originalName": "StartTime",
            "variable": 1
        },
        "rasx.scan_ending_date_time": {
            "name": {
                "ja": "スキャン終了時刻",
                "en": "Scan Ending Date Time"
            },
            "schema": {
                "type": "string"
            },
            "order": 13,
            "mode": "rasx形式",
            "originalName": "EndTime",
            "variable": 1
        },
        "rasx.memo": {
            "name": {
                "ja": "メモ",
                "en": "Memo"
            },
            "schema": {
                "type": "string"
            },
            "order": 14,
            "mode": "rasx形式",
            "originalName": "Memo",
            "variable": 1
        },
        "rasx.measurement_operator": {
            "name": {
                "ja": "測定実施者",
                "en": "Measurement Operator"
            },
            "schema": {
                "type": "string"
            },
            "order": 15,
            "mode": "rasx形式",
            "originalName": "Operator",
            "variable": 1
        },
        "rasx.detector_pixel_size": {
            "name": {
                "ja": "検出器ピクセルサイズ",
                "en": "Detector Pixel Size"
            },
            "schema": {
                "type": "number"
            },
            "order": 16,
            "mode": "rasx形式",
            "originalName": "PixelSize",
            "variable": 1
        },
        "rasx.x-ray_target_material": {
            "name": {
                "ja": "X線ターゲットの材質",
                "en": "X-ray Target Material"
            },
            "schema": {
                "type": "string"
            },
            "order": 17,
            "mode": "rasx形式",
            "originalName": "TargetName",
            "variable": 1
        },
        "rasx.k_alpha_1_wavelength": {
            "name": {
                "ja": "K_alpha1の波長",
                "en": "K_alpha_1 Wavelength"
            },
            "schema": {
                "type": "number"
            },
            "order": 18,
            "unit": "Angstrom",
            "mode": "rasx形式",
            "originalName": "WavelengthKalpha1",
            "variable": 1
        },
        "rasx.k_alpha_2_wavelength": {
            "name": {
                "ja": "K_alpha2の波長",
                "en": "K_alpha_2 Wavelength"
            },
            "schema": {
                "type": "number"
            },
            "order": 19,
            "unit": "Angstrom",
            "mode": "rasx形式",
            "originalName": "WavelengthKalpha2",
            "variable": 1
        },
        "rasx.k_beta_wavelength": {
            "name": {
                "ja": "K_betaの波長",
                "en": "K_beta Wavelength"
            },
            "schema": {
                "type": "number"
            },
            "order": 20,
            "unit": "Angstrom",
            "mode": "rasx形式",
            "originalName": "WavelengthKbeta",
            "variable": 1
        },
        "rasx.optics_attribute": {
            "name": {
                "ja": "光学系属性",
                "en": "Optics Attribute"
            },
            "schema": {
                "type": "string"
            },
            "order": 21,
            "mode": "rasx形式",
            "originalName": "Attribute",
            "variable": 1
        },
        "rasx.wavelength_type": {
            "name": {
                "ja": "波長タイプ",
                "en": "Wavelength Type"
            },
            "schema": {
                "type": "string"
            },
            "order": 22,
            "mode": "rasx形式",
            "originalName": "WaveType",
            "variable": 1
        },
        "rasx.data_point_number": {
            "name": {
                "ja": "データ点数",
                "en": "Data Point Number"
            },
            "schema": {
                "type": "number"
            },
            "order": 23,
            "mode": "rasx形式",
            "originalName": "DataCount",
            "variable": 1
        },
        "rasx.scan_axis_unit": {
            "name": {
                "ja": "スキャン軸の単位",
                "en": "Scan Axis Unit"
            },
            "schema": {
                "type": "string"
            },
            "order": 24,
            "mode": "rasx形式",
            "originalName": "PositionUnit",
            "variable": 1
        },
        "rasx.intensity_unit": {
            "name": {
                "ja": "強度の単位",
                "en": "Intensity Unit"
            },
            "schema": {
                "type": "string"
            },
            "order": 25,
            "mode": "rasx形式",
            "originalName": "IntensityUnit",
            "variable": 1
        }
    }
    metadata_def_path = tmp_path / "metadata-def.json"
    with open(metadata_def_path, mode="w", encoding="utf-8") as f:
        json.dump(metadata_def, f)
    return metadata_def_path


@pytest.fixture
def class_meta(metadata_def):
    return Meta(metadata_def)


@pytest.fixture
def input_meta():
    """入力メタデータ"""
    reader = FileReader(RDE_CONFIG_YAML)
    for _, meta in reader.read(INPUT_FILE):  # MEMO: read内でGeneratorが使われている
        return meta


@pytest.fixture
def parse_meta():
    """構文解析後メタデータ"""
    return {
        'rasx.comment': [''],
        'rasx.measurement_operator': ['nims'],
        'rasx.specimen': [''],
        'rasx.memo': [''],
        'rasx.x-ray_target_material': ['Cu'],
        'rasx.wavelength_type': ['K_alpha'],
        'rasx.x-ray_tube_current': ['15'],
        'CurrentUnit': ['mA'],
        'rasx.x-ray_tube_voltage': ['40'],
        'VoltageUnit': ['kV'],
        'rasx.k_beta_wavelength': ['1.392246'],
        'rasx.k_alpha_1_wavelength': ['1.540593'],
        'rasx.k_alpha_2_wavelength': ['1.544414'],
        'rasx.detector_pixel_size': ['0.1'],
        'rasx.optics_attribute': [''],
        'rasx.scan_axis': ['2Theta-Theta'],
        'rasx.scan_mode': ['CONTINUOUS'],
        'rasx.scan_starting_position': ['1.0000'],
        'rasx.scan_ending_position': ['100.0000'],
        'rasx.scan_step_size': ['0.0100'],
        'rasx.scan_speed': ['3.0000'],
        'SpeedUnit': ['deg/min'],
        'PositionUnit': ['deg'],
        'rasx.intensity_unit': ['counts'],
        'rasx.scan_starting_date_time': ['2022-11-07T01:00:24Z'],
        'rasx.scan_ending_date_time': ['2022-11-07T01:35:20Z'],
        'rasx.data_point_number': ['9901']
    }


@pytest.fixture
def output_meta():
    """ファイル出力後メタデータ"""
    return {
        "constant": {},
        "variable": [{
            'rasx.scan_axis': {'value': '2Theta-Theta'},
            'rasx.scan_mode': {'value': 'CONTINUOUS'},
            'rasx.x-ray_tube_current': {'value': 15, 'unit': 'mA'},
            'rasx.x-ray_tube_voltage': {'value': 40, 'unit': 'kV'},
            'rasx.scan_starting_position': {'value': 1.0, 'unit': 'deg'},
            'rasx.scan_ending_position': {'value': 100.0, 'unit': 'deg'},
            'rasx.scan_step_size': {'value': 0.01, 'unit': 'deg'},
            'rasx.scan_speed': {'value': 3.0, 'unit': 'deg/min'},
            'rasx.scan_starting_date_time': {'value': '2022-11-07T01:00:24Z'},
            'rasx.scan_ending_date_time': {'value': '2022-11-07T01:35:20Z'},
            'rasx.measurement_operator': {'value': 'nims'},
            'rasx.detector_pixel_size': {'value': 0.1},
            'rasx.x-ray_target_material': {'value': 'Cu'},
            'rasx.k_alpha_1_wavelength': {'value': 1.540593, 'unit': 'Angstrom'},
            'rasx.k_alpha_2_wavelength': {'value': 1.544414, 'unit': 'Angstrom'},
            'rasx.k_beta_wavelength': {'value': 1.392246, 'unit': 'Angstrom'},
            'rasx.wavelength_type': {'value': 'K_alpha'},
            'rasx.data_point_number': {'value': 9901},
            'rasx.scan_axis_unit': {'value': 'deg'},
            'rasx.intensity_unit': {'value': 'counts'}
        }]
    }


## inputfile_handler


def test_read(read_data, read_meta):
    """ファイル読み込み"""

    # 正常(標準)
    reader = FileReader(RDE_CONFIG_YAML)
    for data, meta in reader.read(INPUT_FILE):  # MEMO: read内でGeneratorが使われている
        pd.testing.assert_frame_equal(data, read_data)
        assert meta == read_meta

    # データなし
    reader_no_data = FileReader(RDE_CONFIG_YAML)
    with pytest.raises(StructuredError) as e:
        for _, _ in reader_no_data.read(INPUT_EMPTY_FILE):
            pass
    assert str(e.value).startswith("Cannot read the file because it is formatted incorrectly:")


def test_get_region_number():
    """リージョン番号取得"""

    # 引数(標準)
    reader = FileReader(RDE_CONFIG_YAML)
    for _, _ in reader.read(INPUT_FILE):
        region_num = reader.get_region_number()
    assert region_num == SINGLE_REGION_NUM

    # インスタンス変数
    reader_instance = FileReader(RDE_CONFIG_YAML)
    reader_instance.region_num = SINGLE_REGION_NUM
    region_num_instance = reader_instance.get_region_number()
    assert region_num_instance == reader.region_num


def test_get_metadata(read_meta):
    """メタデータ取得"""

    # 正常(標準)
    reader = FileReader(RDE_CONFIG_YAML)
    meta = reader.get_metadata(INPUT_FILE)
    assert meta['Data0/MesurementConditions0.xml'] == read_meta


def test_get_data(input_data):
    """計測データ取得"""
    reader = FileReader(RDE_CONFIG_YAML)
    data = reader.get_data(INPUT_FILE)
    pd.testing.assert_frame_equal(data['Data0/Profile0.txt'], input_data)


def test_make_header(read_meta):
    """グラフのラベルを作成"""
    reader = FileReader(RDE_CONFIG_YAML)

    # ラベルをカスタムしない(標準)
    header = reader.make_header(read_meta)
    assert header == ['2Theta-Theta (deg)', 'Intensity (counts)']

    # ラベルをカスタムする
    config: dict = {
        'system': {
            'magic_variable': True,
            'save_thumbnail_image': True,
        },
        'xrd': {
            'filename_mapping_rule': True,
            'manufacturer': 'rigaku',
            'main_image_setting': None,
            'meas_scan_axis_x': "XXX",
            'meas_scan_unit_x': "width",
            'meas_scan_axis_y': "YYY",
            'meas_scan_unit_y': "height"
        }
    }
    reader_custom = FileReader(config)
    header_custom = reader_custom.make_header(read_meta)
    assert header_custom == ['XXX (width)', 'YYY (height)']


def test_reformat_dataframe(input_data, read_data):
    """計測データのデータフレーム化"""
    reader = FileReader(RDE_CONFIG_YAML)
    data = reader.reformat_dataframe(input_data, header=['2Theta-Theta (deg)', 'Intensity (counts)'])
    pd.testing.assert_frame_equal(data, read_data)


def test_get_files_from_rasx():
    """圧縮ファイル内の一覧取得"""
    reader = FileReader(RDE_CONFIG_YAML)
    files = reader.get_files_from_rasx(INPUT_FILE)
    assert files == ['Data0/Profile0.txt', 'Data0/MesurementConditions0.xml']


def test_open_file(temp_dir):
    """圧縮ファイル読み込み"""
    reader = FileReader(RDE_CONFIG_YAML)

    with zipfile.ZipFile(str(INPUT_EMPTY_FILE), "r") as rasx:
        root_xml_files = [name for name in rasx.namelist() if name.startswith("test.")]
    for root_xml_file in root_xml_files:
        assert not reader.open_file(root_xml_file, INPUT_EMPTY_FILE)


def test_open_compressedfile_dataframe(input_data):
    """圧縮ファイルからのデータフレーム読み込み"""
    reader = FileReader(RDE_CONFIG_YAML)
    data = reader.open_compressedfile_dataframe('Data0/Profile0.txt', INPUT_FILE)
    pd.testing.assert_frame_equal(data, input_data)


## meta_handler


def test_parse(input_meta, metadata_def, parse_meta):
    """構文解析"""

    # 引数(標準)
    handler = MetaParser(metadata_def_json_path=metadata_def, config=RDE_CONFIG_YAML)
    _, repeated_meta_info = handler.parse(input_meta)
    assert repeated_meta_info == parse_meta

    # インスタンス変数
    handler_instance = MetaParser(metadata_def_json_path=metadata_def, config=RDE_CONFIG_YAML)
    handler_instance.repeated_meta_info = input_meta
    _, repeated_meta_info_instance = handler_instance.parse(None)
    assert repeated_meta_info_instance == handler_instance.repeated_meta_info


def test_save_meta(temp_dir, class_meta, parse_meta, output_meta):
    """csvファイル出力(引数)"""
    metadata_def = temp_dir / "metadata-def.json"
    save_path = temp_dir / "metadata.json"

    # 引数(標準)
    repeated_meta_info = parse_meta
    handler = MetaParser(metadata_def_json_path=metadata_def, config=RDE_CONFIG_YAML)
    _ = handler.save_meta(save_path, class_meta, repeated_meta_info=repeated_meta_info)
    assert os.path.exists(save_path)
    with open(save_path, "r", encoding="utf-8") as f:
        contents = json.load(f)
    assert contents == output_meta

    if os.path.exists(save_path):
        os.remove(save_path)

    # インスタンス変数
    handler_instance = MetaParser(metadata_def_json_path=metadata_def, config=RDE_CONFIG_YAML)
    handler_instance.repeated_meta_info = parse_meta
    _ = handler_instance.save_meta(save_path, class_meta)
    assert os.path.exists(save_path)
    with open(save_path, "r", encoding="utf-8") as f:
        contents_instance = json.load(f)
    assert contents_instance == output_meta

    if os.path.exists(save_path):
        os.remove(save_path)


def test_load_invoice_file(metadata_def, class_meta):
    """インボイスをメタに展開"""
    # MEMO:インスタンス生成時点でload_invoice_fileがcallされている
    handler = MetaParser(metadata_def_json_path=metadata_def, config=RDE_CONFIG_YAML)
    assert handler.meta_def_obj == class_meta.metaDef
