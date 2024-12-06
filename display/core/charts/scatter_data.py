import collections
from dataclasses import dataclass
from typing import List

from display.webapp.app.models import Defacements


@dataclass
class ScatterChartData:
    name: str
    x: List[str]
    y: List[str]
    type: str = "scatter"


@dataclass
class DefacementsContainer:
    data: List[Defacements]

    @property
    def defacements_per_header(self) -> dict[str, List[Defacements]]:
        ret_dict = collections.defaultdict(list)
        for each in self.data:
            ret_dict[each.header].append(each)
        return dict(ret_dict)

    @property
    def scatterchartdata_per_header(self) -> List[ScatterChartData]:
        ret_list = []
        for header, defacement_data in self.defacements_per_header.items():
            ret_list.append(
                ScatterChartData(
                    name=header,
                    x=[x.created_at for x in defacement_data],
                    y=[x.count for x in defacement_data],
                )
            )
        return ret_list
