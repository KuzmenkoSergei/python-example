# -*- coding: utf-8 -*-
import json
import csv
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.http import HttpResponse
from .utils import CsvIo


csv.register_dialect('csv', delimiter='|')


class JsonTableView(LoginRequiredMixin, generic.ListView):

    def get(self, request):
        mcc_mnc_map_objects = CsvIo().get_mcc_mnc_map()
        network_prefix_objects = CsvIo().get_gt_network_prefix_map()
        common_map = []
        for item_map in mcc_mnc_map_objects:
            if item_map[0].isdigit() and item_map[1].isdigit():
                has_number = False
                for item in network_prefix_objects:
                    if int(item[1]) == int(item_map[0]) and int(item[2]) == int(item_map[1]):
                        common_map.append([item_map[0], item_map[1], item_map[3], item_map[2], item[0]])
                        has_number = True
                if not has_number:
                    common_map.append([item_map[0], item_map[1], item_map[3], item_map[2], ""])
        results = []
        for i in common_map:
            results.append({"mcc": i[0], "mnc": i[1], "operator": i[2], "country": i[3], "number": i[4]})
        return HttpResponse(json.dumps(results, encoding="utf-8"), content_type="application/json")


class IndexView(LoginRequiredMixin, generic.TemplateView):
    login_url = 'login'
    redirect_field_name = 'redirect_to'
    template_name = 'csv_table/index.html'


class AddFormView(LoginRequiredMixin, generic.View):
    def post(self, request, *args, **kwargs):
        if len(request.POST["mcc"]) != 0 and len(request.POST['mnc']) != 0:
            mcc_mnc_map_list = CsvIo().get_mcc_mnc_map()
            network_prefix_list = CsvIo().get_gt_network_prefix_map()
            request_dict = dict(request.POST)
            request_dict = {k: ''.join([x for x in v]) for k, v in request_dict.items()}
            if request_dict["mnc"].isdigit() and len(request_dict["mnc"]) == 1:
                request_dict["mnc"] = "0"+request_dict["mnc"]
            if request_dict["mcc"].isdigit() and len(request_dict["mcc"]) == 1:
                request_dict["mcc"] = "0" + request_dict["mcc"]
            for iter_map in mcc_mnc_map_list:
                if request_dict["mcc"] == iter_map[0] and \
                                request_dict["mnc"] == iter_map[1] and len(request_dict["number"]) == 0:
                    return HttpResponse("such mcc and mnc is already exist")
            mcc_mnc_row_holder = []
            is_in_mcc_mnc_map = False
            is_in_gt_net_map = False
            for iter_map in mcc_mnc_map_list:
                if request_dict["mcc"] == iter_map[0] and request_dict["mnc"] == iter_map[1]:
                    mcc_mnc_row_holder = iter_map
                    is_in_mcc_mnc_map = True
            if is_in_mcc_mnc_map:
                for iter in network_prefix_list:
                    if request_dict["number"].encode("utf-8") in iter and mcc_mnc_row_holder[0] == iter[1].encode() and mcc_mnc_row_holder[1] == iter[2].encode():
                        is_in_gt_net_map = True
            else:
                request_dict["mcc"] = str(int(request_dict["mcc"]))
                if len(request_dict["mcc"]) == 1:
                    request_dict["mcc"] = "0"+request_dict["mcc"]
                request_dict["mnc"] = str(int(request_dict["mnc"]))
                if len(request_dict["mnc"]) == 1:
                    request_dict["mnc"] = "0" + request_dict["mnc"]
                mcc_mnc_map_list.append([request_dict["mcc"], request_dict["mnc"], request_dict["country"],
                                            request_dict["operator"]])

            if is_in_gt_net_map:
                return HttpResponse("such record is already exists")
            else:
                request_dict["mcc"] = str(int(request_dict["mcc"]))
                if len(request_dict["mcc"]) == 1:
                    request_dict["mcc"] = "0" + request_dict["mcc"]
                request_dict["mnc"] = str(int(request_dict["mnc"]))
                if len(request_dict["mnc"]) == 1:
                    request_dict["mnc"] = "0" + request_dict["mnc"]
                if len(mcc_mnc_row_holder) != 0 and len(request_dict["number"]) != 0:
                    network_prefix_list.append([request_dict["number"], request_dict["mcc"], request_dict["mnc"],
                                               mcc_mnc_row_holder[3]])
                else:
                    if len(request_dict["number"]) != 0:
                        network_prefix_list.append([request_dict["number"], request_dict["mcc"], request_dict["mnc"],
                                                    request_dict["operator"]])
            mcc_res = CsvIo().save_mcc_mnc_map(mcc_mnc_map_list)
            if len(request_dict["number"]) != 0:
                gt_network_res = CsvIo().save_gt_network_prefix_map(network_prefix_list)
                if gt_network_res is False or mcc_res is False:
                    return HttpResponse("Incorrect request...Data was not added!")

            return HttpResponse("Data was successfully added")
        else:
            return HttpResponse("mcc and mnc parameters are required... Data was not added!")


class EditFormView(LoginRequiredMixin, generic.View):
    def post(self, request, *args, **kwargs):
        if len(request.POST["mcc"]) != 0 and len(request.POST['mnc']) != 0:
            mcc_mnc_map_list = CsvIo().get_mcc_mnc_map()
            network_prefix_list = CsvIo().get_gt_network_prefix_map()
            request_dict = dict(request.POST)
            mcc_mnc_row_holder = []
            request_dict = {k: ''.join([x for x in v]) for k, v in request_dict.items()}
            if request_dict["mnc"].isdigit() and len(request_dict["mnc"]) == 1:
                request_dict["mnc"] = "0" + request_dict["mnc"]
            if request_dict["mcc"].isdigit() and len(request_dict["mcc"]) == 1:
                request_dict["mcc"] = "0" + request_dict["mcc"]
            is_in_mcc = False
            for iter_map in mcc_mnc_map_list:
                if request_dict["mcc"].encode() == iter_map[0] and \
                                request_dict["mnc"].encode() == iter_map[1]:
                    is_in_mcc = True
                    if request_dict["country"] != iter_map[2]:
                        iter_map[2] = str(request_dict["country"])
                    if request_dict["operator"] != iter_map[3]:
                        iter_map[3] = str(request_dict["operator"])
                    mcc_mnc_row_holder = iter_map
            is_in_gt_network = False
            for iter in network_prefix_list:
                if is_in_mcc:
                    if not is_in_gt_network:
                        if request_dict["operator"].encode() != iter[3] and request_dict["mcc"].encode() == iter[1] \
                                and request_dict["mnc"].encode() == iter[2]:
                            iter[3] = request_dict["operator"]
                        if iter[0].isdigit() and len(iter[0]) > 0:
                            if str(request_dict["which_number"]) == str(iter[0]) and\
                                            int(request_dict["mcc"].encode()) == int(iter[1]) and\
                                                int(request_dict["mnc"]) == int(iter[2]):
                                iter[0] = request_dict["number"]
                                iter[3] = mcc_mnc_row_holder[3]
                                is_in_gt_network = True
                        else:
                            if len(request_dict["which_number"].encode()) == iter[0] and\
                                            int(request_dict["mcc"].encode()) == int(iter[1])and\
                                                int(request_dict["mnc"]) == int(iter[2]):
                                iter[0] = request_dict["which_number"]
                                iter[3] = mcc_mnc_row_holder[3]
                                is_in_gt_network = True
                    else:
                        if int(request_dict["mcc"].encode()) == int(iter[1]) and \
                                        int(request_dict["mnc"].encode()) == int(iter[2]):
                            if len(mcc_mnc_row_holder) != 0:
                                iter[3] = mcc_mnc_row_holder[3]
                            else:
                                iter[3] = request_dict["operator"]
                else:
                    return HttpResponse("No such mcc/mnc, try to add them before edit")
            if is_in_mcc and not is_in_gt_network and len(request_dict["number"].encode()) != 0:
                network_prefix_list.append([request_dict['number'].encode(), request_dict['mcc'].encode(),
                                            request_dict['mnc'].encode(), request_dict['operator'].encode()])
            mcc_res = CsvIo().save_mcc_mnc_map(mcc_mnc_map_list)
            gt_network_res = CsvIo().save_gt_network_prefix_map(network_prefix_list)

            if gt_network_res is False or mcc_res is False:
                return HttpResponse("Incorrect request...Data was not edited!")

            return HttpResponse("Record is successfully edited")
        else:
            return HttpResponse("Incorrect request...Data was not edited!")


class DeleteFormView(LoginRequiredMixin, generic.View):

    def post(self, request, *args, **kwargs):

        mcc_mnc_map_list = CsvIo().get_mcc_mnc_map()
        network_prefix_list = CsvIo().get_gt_network_prefix_map()

        request_dict = dict(request.POST)
        request_dict = {k: ''.join([x for x in v]) for k, v in request_dict.items()}
        if request_dict["mnc"].isdigit() and len(request_dict["mnc"]) == 1:
            request_dict["mnc"] = "0" + request_dict["mnc"]
        if request_dict["mcc"].isdigit() and len(request_dict["mcc"]) == 1:
            request_dict["mcc"] = "0" + request_dict["mcc"]

        network_prefix_result = []
        mcc_mnc_map_result = []

        double_number_counter = 0
        mcc_mnc_repeats_counter = 0
        for iter in network_prefix_list:
            if int(request_dict["mcc"].encode()) == int(iter[1]) and \
                            int(request_dict["mnc"].encode()) == int(iter[2]):
                mcc_mnc_repeats_counter += 1
            if request_dict["which_number"].encode() != iter[0]:
                network_prefix_result.append(iter)
            else:
                if double_number_counter < 1:
                    if request_dict["mcc"].encode() != iter[1] and request_dict["mnc"].encode() != iter[2]:
                        network_prefix_result.append(iter)
                    else:
                        # skip only one record if there are duplicates
                        double_number_counter += 1
                else:
                    network_prefix_result.append(iter)

        for iter_map in mcc_mnc_map_list:
            if mcc_mnc_repeats_counter > 1:
                mcc_mnc_map_result.append(iter_map)
            else:
                if iter_map[0].isdigit() and iter_map[1].isdigit():
                    if str(int(request_dict["mcc"].encode())) != str(int(iter_map[0])) or\
                                    str(int(request_dict["mnc"].encode())) != str(int(iter_map[1])):
                        mcc_mnc_map_result.append(iter_map)
                else:
                    if request_dict["mcc"].encode != iter_map[0] or request_dict["mnc"].encode() != iter_map[1]:
                        mcc_mnc_map_result.append(iter_map)

        mcc_res = CsvIo().save_mcc_mnc_map(mcc_mnc_map_result)
        gt_network_res = CsvIo().save_gt_network_prefix_map(network_prefix_result)

        if gt_network_res is False or mcc_res is False:
            return HttpResponse("Incorrect request...Data was not deleted!")

        return HttpResponse("Record was successfully deleted")