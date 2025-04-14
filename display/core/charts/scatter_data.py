import collections
from dataclasses import dataclass, field
from datetime import datetime

from display.webapp.app.models import Defacements


@dataclass
class ScatterChartData:
    name: str
    x: list[str]
    y: list[str]
    hovertemplate: str = field(init=False)
    type: str = "scatter"

    def __post_init__(self):
        self.hovertemplate = f"<b>{self.name}</b><br>At: %{{x}}<br>Defacements: %{{y}}"


@dataclass
class DefacementsContainer:
    data: list[Defacements]

    @property
    def defacements_per_header(self) -> dict[str, list[Defacements]]:
        ret_dict = collections.defaultdict(list)
        for each in self.data:
            ret_dict[each.header].append(each)
        return dict(ret_dict)

    @property
    def scatterchartdata_per_header(self) -> list[ScatterChartData]:
        ret_list = []
        for header, defacement_data in self.defacements_per_header.items():
            ret_list.append(
                ScatterChartData(
                    name=header,
                    x=[
                        datetime.fromtimestamp(x.created_at).strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        )
                        for x in defacement_data
                    ],
                    y=[x.count for x in defacement_data],
                )
            )
        return ret_list
