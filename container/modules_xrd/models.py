"""Group of data classes corresponding to XML structure.

xml files (root.xml, DataX/MesurementConditions*.xml) stored in rasx
Tag information is mapped to data classes

Profile*.xml is not applicable because it stores only measurement data.

"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, field_validator
from pydantic_xml import BaseXmlModel, attr, element


class ScaleType(Enum):
    log = "log"
    linear = "linear"


class Data0(BaseXmlModel):
    """XML elements of root.xml."""

    contenthashlist: list[dict[str, str]] = element(tag="ContentHashList")


class Data1(BaseXmlModel):
    """XML elements of root.xml."""

    contenthashlist: list[dict[str, str]] = element(tag="ContentHashList")


class Root(BaseXmlModel, search_mode='unordered'):
    """XML elements of root.xml."""

    data0: Data0 | None = element(tag="Data0")
    data1: Data1 | None = element(tag="Data1", default=None)


class Category(BaseXmlModel, search_mode='unordered'):
    """XML elements of MesurementConditions*.xml."""

    Name: str = attr(name="Name", default='')
    SelectedUnit: str = attr(name="SelectedUnit", default='')


class Distance(BaseXmlModel, search_mode='unordered'):
    """XML elements of MesurementConditions*.xml."""

    To: str = attr(name="To", default='')
    From: str = attr(name="From", default='')
    Unit: str = attr(name="Unit", default='')
    Value: str = attr(name="Value", default='')


class Categories(BaseXmlModel):
    """XML elements of MesurementConditions*.xml."""

    category: list[Category] = element(tag="Category")


class Distances(BaseXmlModel):
    """XML elements of MesurementConditions*.xml."""

    distance: list[Distance] = element(tag="Distance")


class XrayGenerator(BaseXmlModel, BaseModel, search_mode='unordered'):
    """XML elements of MesurementConditions*.xml."""

    Type: str = element(tag="Type", default='')
    FocusSize: str = element(tag="FocusSize", default='')
    FocusType: str = element(tag="FocusType", default='')
    TargetAtomicNumber: str = element(tag="TargetAtomicNumber", default='')
    TargetName: str = element(tag="TargetName", default='')
    WaveType: str = element(tag="WaveType", default='')
    Current: str = element(tag="Current", default='')
    CurrentUnit: str = element(tag="CurrentUnit", default='')
    Voltage: str = element(tag="Voltage", default='')
    VoltageUnit: str = element(tag="VoltageUnit", default='')
    WavelengthKbeta: str = element(tag="WavelengthKbeta", default='')
    WavelengthKalpha1: str = element(tag="WavelengthKalpha1", default='')
    WavelengthKalpha2: str = element(tag="WavelengthKalpha2", default='')

    @field_validator("WaveType")
    def replace_geek_char(cls, v: str | None) -> str | None:
        """Replace geek char."""
        if v:
            return v.replace("a", "_alpha").replace("b", "_beta")
        return v


class Detector(BaseXmlModel, search_mode='unordered'):
    """XML elements of MesurementConditions*.xml."""

    PHAUnit: str = element(tag="PHAUnit", default='')
    PHABase: str = element(tag="PHABase", default='')
    PHAWindow: str = element(tag="PHAWindow", default='')
    PixelSize: str = element(tag="PixelSize", default='')


class Optics(BaseXmlModel, search_mode='unordered'):
    """XML elements of MesurementConditions*.xml."""

    Name: str = element(tag="Name", default='')
    Attribute: str = element(tag="Attribute", default='')


class HWConfigurations(BaseXmlModel, search_mode='unordered'):
    """XML elements of MesurementConditions*.xml."""

    categories: Categories | None = element(tag="Categories")
    distances: Distances | None = element(tag="Distances")
    xraygenerator: XrayGenerator | None = element(tag="XrayGenerator")
    detector: Detector | None = element(tag="Detector")
    optics: Optics | None = element(tag="Optics", default="")


class Axis(BaseXmlModel):
    """XML elements of MesurementConditions*.xml."""

    Name: str = attr(name="Name", default='')
    Unit: str = attr(name="Unit", default='')
    Offset: str = attr(name="Offset", default='')
    Position: str = attr(name="Position", default='')
    State: str = attr(name="State", default='')
    Resolution: str = attr(name="Resolution", default='')


class Axes(BaseXmlModel):
    """XML elements of MesurementConditions*.xml."""

    axis: list[Axis] | None = element(tag="Axis")


class GeneralInformation(BaseXmlModel, search_mode='unordered'):
    """XML elements of MesurementConditions*.xml."""

    Comment: str = element(tag="Comment", default='')
    Operator: str = element(tag="Operator", default='')
    PackageName: str = element(tag="PackageName", default='')
    PartName: str = element(tag="PartName", default='')
    SampleName: str = element(tag="SampleName", default='')
    Type: str = element(tag="Type", default='')
    SystemName: str = element(tag="SystemName", default='')
    UserGroup: str = element(tag="UserGroup", default='')
    Version: str = element(tag="Version", default='')
    Memo: str = element(tag="Memo", default='')


class ScanInformation(BaseXmlModel, BaseModel, search_mode='unordered'):
    """XML elements of MesurementConditions*.xml."""

    AxisName: str = element(tag="AxisName")
    Mode: str = element(tag="Mode", default='')
    Start: str = element(tag="Start", default='')
    Stop: str = element(tag="Stop", default='')
    Step: str = element(tag="Step", default='')
    Speed: str = element(tag="Speed", default='')
    Resolution: str = element(tag="Resolution", default='')
    SpeedUnit: str = element(tag="SpeedUnit", default='')
    PositionUnit: str = element(tag="PositionUnit", default='')
    IntensityUnit: str = element(tag="IntensityUnit", default='')
    StartTime: str = element(tag="StartTime", default='')
    EndTime: str = element(tag="EndTime", default='')
    AttenuatorAutoMode: bool = element(tag="AttenuatorAutoMode", default_factory=bool)
    UnequalySpaced: bool = element(tag="UnequalySpaced", default_factory=bool)
    DataCount: str = element(tag="DataCount", default='')
    DscStartTime: str = element(tag="DscStartTime", default='')
    DscEndTime: str = element(tag="DscEndTime", default='')

    @field_validator("AxisName")
    def replace_geek_char(cls, v: str) -> str:
        """Replace geek char."""
        if v is not None:
            return v.replace("TwoThetaTheta", "2Theta-Theta").replace("2θ/θ", "2Theta-Theta")
        return v


class String(BaseXmlModel):
    string: str = element(tag="string", default="")


class RASHeader(BaseXmlModel, tag="RASHeader"):
    """XML elements of MesurementConditions*.xml."""

    Pair: list[String] = element(tag="Pair", default=[])


class MeasurementConditions(BaseXmlModel, search_mode='unordered'):
    """XML elements of MesurementConditions*.xml."""

    generalinformation: GeneralInformation = element(tag="GeneralInformation")
    hwconfigurations: HWConfigurations = element(tag="HWConfigurations")
    axes: Axes = element(tag="Axes")
    scaninformation: ScanInformation = element(tag="ScanInformation")
    rasheader: RASHeader
    sampleinformation: str = element(tag="SampleInformation", default='')
