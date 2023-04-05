"""
server_side_dt.py
================
"""
import sre_constants
from collections import namedtuple, defaultdict
import re


class ServerSideDataTable(object):
    """
    This class holds all the logic for enabling and handling server side DataTables within the Display application

    """

    def __init__(
            self,
            request,
            backend,
    ):

        self.request_values = request.values

        self.backend = backend

        self.columns, self.ordering, self.results, self.fields, self.data_length = (
            None,
            None,
            None,
            None,
            None,
        )

        self.total, self.total_filtered, self.current_draw = 0, 0, 0

        self.filtered = {}

        self.sort = []

        self._pre_fetch_processing()

    def output_result(self):

        retdata = {
            "draw": int(self.current_draw),
            "recordsTotal": int(self.total),
            "recordsFiltered": int(self.total_filtered),
            "data": self.results,
        }

        return retdata

    def _pre_fetch_processing(self):
        """
        Method to provision the necessary variables for the correct retrieval of the results from the MongoDB Database
        """

        self.current_draw = int(self.request_values["draw"])

        self.data_length = self.__data_dimension()

        self.columns, self.ordering = self.__data_columns_ordering()

        # for each in self.ordering:
        #     if self.ordering[each]["dir"] == "asc":
        #         self.sort.append(
        #             (
        #                 self.columns[self.ordering[each]["column"]]["data"],
        #                 pymongo.ASCENDING,
        #             )
        #         )
        #     else:
        #         self.sort.append(
        #             (
        #                 self.columns[self.ordering[each]["column"]]["data"],
        #                 pymongo.DESCENDING,
        #             )
        #         )

        self.fields = defaultdict(int)

        for each in self.columns:
            self.fields[self.columns[each]["data"]] = 1

        self.fields["_id"] = self.add_id

        if len(self.sort) == 0:
            self.sort = None

        self.total = self.backend.count()

        self.filtered = self.__data_filter()

        self._fetch_results()

        if len(self.filtered) != 0:
            self.total_filtered = self.backend.count(self.filtered)
        else:
            self.total_filtered = self.total

        self._post_fetch_processing()

    def _fetch_results(self):
        """
        Method responsible for querying the backend and fetching the results from the database
        """

        self.results = []

    def _post_fetch_processing(self):
        if len(self.post_fetch_actions) != 0:
            for each in self.post_fetch_actions:
                getattr(self, f"_{each}")()

    def __data_dimension(self):
        """
        Method responsible for retrieving the requested start and length parameters from the DataTables request values

        :return: Namedtuple 'data_length' with a start and length attribute
        :rtype: namedtuple
        """

        data_length = namedtuple("data_length", ["start", "length"])

        data_length.start = int(self.request_values["start"])
        data_length.length = int(self.request_values["length"])

        return data_length

    def __data_columns_ordering(self):
        """
        Method responsible for retrieving the column and order details from the DataTables request values

        :return: 2 Dictionaries the column details and order details
        :rtype: defaultdict, defaultdict
        """

        col = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        order = defaultdict(lambda: defaultdict(dict))

        col_regex = re.compile(r"columns\[(\d*)\]\[(\w*)\](?:\[(\w*)\])?")
        order_regex = re.compile(r"order\[(\d*)\]\[(\w*)\]")

        for each in sorted(self.request_values.keys()):
            check_col_match = col_regex.match(each)
            check_order_match = order_regex.match(each)
            if check_col_match:
                if check_col_match.group(2) == "search":
                    try:
                        col[check_col_match.group(1)][check_col_match.group(2)][
                            check_col_match.group(3)
                        ] = int(self.request_values[each])
                    except ValueError:
                        col[check_col_match.group(1)][check_col_match.group(2)][
                            check_col_match.group(3)
                        ] = self.request_values[each]
                else:
                    col[check_col_match.group(1)][
                        check_col_match.group(2)
                    ] = self.request_values[each]
            if check_order_match:
                order[check_order_match.group(1)][
                    check_order_match.group(2)
                ] = self.request_values[each]

        return col, order

    def __data_filter(self):
        """
        Method responsible for retrieving the filter values entered in the search box of the DataTables.

        :return: Prepared filter based on filterable columns and retrieved search value
        :rtype: dict
        """

        docfilter = defaultdict(list)

        search_val = self.request_values["search[value]"]

        if search_val != "" and search_val != "$":

            try:
                regex = re.compile(search_val, re.IGNORECASE)

                # get list with searchable columns
                column_search_list = [
                    self.columns[i]["data"]
                    for i in self.columns
                    if self.columns[i]["searchable"]
                ]

                for each in column_search_list:
                    docfilter["$or"].append(
                        {
                            "$expr": {
                                "$regexMatch": {
                                    "input": {"$toString": f"${each}"},
                                    "regex": search_val,
                                }
                            }
                        }
                    )
            except sre_constants.error:
                pass

        # create an additional column filter with entries in the columns[x]['search']['value']

        colfilter = {
            self.columns[key]["data"]: self.columns[key]["search"]["value"]
            for (key, value) in self.columns.items()
            if (
                    self.columns[key]["search"]["value"] != ""
                    and self.columns[key]["search"]["regex"] == "false"
            )
        }

        colregexfilter = {
            self.columns[key]["data"]: {"$regex": self.columns[key]["search"]["value"]}
            for (key, value) in self.columns.items()
            if (
                    self.columns[key]["search"]["value"] != ""
                    and self.columns[key]["search"]["regex"] == "true"
            )
        }

        if len(colfilter) != 0:
            docfilter["$and"].append(colfilter)

        if len(colregexfilter) != 0:
            docfilter["$and"].append(colregexfilter)

        return docfilter
