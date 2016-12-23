import csv
from csv_editor_base.settings import CSVFILES_FOLDER

class CsvIo:

    def get_mcc_mnc_map(self):
        with open(CSVFILES_FOLDER+"\mcc_mnc_map.csv", "rb") as mcc_mnc_file:
            reader = csv.reader(mcc_mnc_file, dialect="csv", delimiter="|")
            mcc_mnc_map_list = (list(reader))
        mcc_mnc_file.close()
        return [x for x in mcc_mnc_map_list if x]

    def get_gt_network_prefix_map(self):
        with open(CSVFILES_FOLDER+"\gt_network_prefix_map.csv", "rb") as network_prefix_objects_file:
            reader = csv.reader(network_prefix_objects_file, dialect="csv", delimiter="|")
            network_prefix_list = (list(reader))
        network_prefix_objects_file.close()
        return [x for x in network_prefix_list if x]

    def save_mcc_mnc_map(self,mcc_mnc_map_list):
        if len(mcc_mnc_map_list) != 0:
            mcc_mnc_map_res = [list(mcc_mnc_map_list)]
            with open(CSVFILES_FOLDER+'\mcc_mnc_map.csv', 'wb') as csvfile:
                mccwriter = csv.writer(csvfile, delimiter='|')
                for mccrow in mcc_mnc_map_res:
                    for mc in mccrow:
                        mccwriter.writerow(mc)
            csvfile.close()
            return True
        else:
            return False

    def save_gt_network_prefix_map(self, network_prefix_list):
            network_prefix_res = [list(network_prefix_list)]
            if len(network_prefix_list) != 0:
                with open(CSVFILES_FOLDER+'\gt_network_prefix_map.csv', "wb") as netw_csv:
                    netwriter = csv.writer(netw_csv, delimiter='|')
                    for netrow in network_prefix_res:
                        for nt in netrow:
                            netwriter.writerow(nt)
                netw_csv.close()
                return True
            else:
                return False
