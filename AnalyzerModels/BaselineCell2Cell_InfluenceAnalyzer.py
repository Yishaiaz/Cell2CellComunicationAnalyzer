import csv
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Tuple, List, Sequence, Iterable, Dict, Set
from Miscellaneous.utils import *
from Miscellaneous.global_parameters import *


class BaselineCell2CellInfluenceAnalyzer:
    def __init__(self, file_full_path: str, **kwargs: Dict[str, object]) -> None:
        """
        possible kwargs:
            'metadata_file_full_path': str, the full path to the metadata file of all experiments
            'threshold_dist': int, the threshold for distance between cells beyond no cell2cell
                communication can occur (relevant to the experiment)
            'distance_metric_from_true_times_of_death': str, for the 'utils.calc_distance_metric_between_signals' function.
                possible values - rmse, mse, kl-divergence, euclidean distance (returns distances mean).
        :param file_full_path: str, the full path of the experiment csv file
        :param kwargs:
        """
        self.file_full_path = file_full_path
        self.exp_name = self.file_full_path.split(os.sep)[-1]
        self.exp_df = pd.read_csv(self.file_full_path)
        # self.full_path_to_experiments_metadata_file = kwargs.get('metadata_file_full_path', METADATA_FILE_FULL_PATH)
        # self.exp_treatment_name, self.exp_temporal_resolution = get_exp_treatment_type_and_temporal_resolution(
        #     exp_file_name=self.exp_name, meta_data_file_full_path=self.full_path_to_experiments_metadata_file)

        self._cell_number = len(self.exp_df)
        self._cells_xy = self.exp_df.loc[:, ['cell_x', 'cell_y']].values
        self._cells_death_times = self.exp_df.loc[:, ['death_time']].values.flatten()
        self._normalized_cell_death_times = normalize(self._cells_death_times, normalization_method='z_score')

        self.frames_number = len(self._cells_death_times)

        self.all_frames_idx = np.arange(0, self.frames_number, 1)
        # self.all_frames_by_minutes = np.arange(self._cells_death_times.min(), self._cells_death_times.max(),
        #                                        self.exp_temporal_resolution)

        self.cells_neighbors_distance_threshold = kwargs.get('threshold_dist', DIST_THRESHOLD_IN_PIXELS)
        self._cells_neighbors_list1, self._cells_neighbors_list2, self._cells_neighbors_list3 = \
            get_cells_neighbors(XY=self._cells_xy, threshold_dist=self.cells_neighbors_distance_threshold)

        self._distance_metric = kwargs.get('distance_metric_from_true_times_of_death', 'rmse')

        self.median_error_by_cell_dist = 0
        self.mean_error_by_cell_dist = 0

        self._base_line_calculated = False

    def calc_prediction_error(self, **kwargs) -> Tuple[float, float]:
        """
        Calculates the baseline prediction for cell death.
        calculates for each cell death, the median and mean times of death of all neighbor cells.
        the distance (according to the distance measurement configured) is returned (and stored as
        an instance attribute).
        for both median and mean calculations.
        the median and mean calculations of each cell are stored in a numpy array as an attribute
        of the instance ('self.median_by_cell_dist' & 'self.mean_by_cell_dist') for later use.

        Note that if a cell has no neighbors (as all topological neighbors are distant
        further than the threshold configured), it is not considered for the baseline calculations, as it is
        considered to be non-affected by other cells.

        :return:
        """
        median_by_cell = list()
        mean_by_cell = list()
        cells_with_no_neighbors_indices = list()

        cell_death_times = self._normalized_cell_death_times if kwargs.get('use_normalized_TOD', True) else self._cells_death_times

        for curr_cell_idx, curr_cell_time_of_death in enumerate(cell_death_times):
            curr_cell_neighbors_indices = self._cells_neighbors_list1[curr_cell_idx]
            curr_cell_neighbors_times_of_death = cell_death_times[curr_cell_neighbors_indices].flatten()
            # verify that curr cell has neighbors ("lone cell"), if it does not, ignore that cell as we can not perform prediction based on zero data
            # to ignore that cell in future calculations, we remove it from the cell death list entirely by keeping a list of cells' indices which had no neighbors
            if len(curr_cell_neighbors_times_of_death) == 0:
                cells_with_no_neighbors_indices.append(curr_cell_idx)
                continue

            median_by_cell.append(np.median(curr_cell_neighbors_times_of_death))
            mean_by_cell.append(np.mean(curr_cell_neighbors_times_of_death))

        median_by_cell = np.array(median_by_cell)
        mean_by_cell = np.array(mean_by_cell)

        loner_cells_mask = np.ones(len(cell_death_times), dtype=bool)
        loner_cells_mask[cells_with_no_neighbors_indices] = False
        cells_times_of_death_with_no_loner_cells = cell_death_times[loner_cells_mask, ...]

        # for kl_divergence metric, in order to remove negative values (as a result of z-score normalization)
        # we add the minimum value in the array and add 0.1 to make sure there won't be zero values
        # for the kl_divergence calculation
        if self._distance_metric == 'kl_divergence':
            cells_times_of_death_with_no_loner_cells = cells_times_of_death_with_no_loner_cells +\
                                                       abs(min(cells_times_of_death_with_no_loner_cells)) + 0.1

            median_by_cell = median_by_cell + abs(min(median_by_cell)) + 0.1
            mean_by_cell = mean_by_cell + abs(min(mean_by_cell)) + 0.1

        # function from utils script
        self.median_error_by_cell_dist = calc_distance_metric_between_signals(y_true=cells_times_of_death_with_no_loner_cells,
                                                                              y_pred=median_by_cell,
                                                                              metric=self._distance_metric)
        self.mean_error_by_cell_dist = calc_distance_metric_between_signals(y_true=cells_times_of_death_with_no_loner_cells,
                                                                            y_pred=mean_by_cell,
                                                                            metric=self._distance_metric)

        self._base_line_calculated = True

        return self.median_error_by_cell_dist, self.mean_error_by_cell_dist

    @staticmethod
    def multiple_experiments_of_treatment_error(full_treatment_type: str,
                                                meta_data_full_file_path: str,
                                                all_experiments_dir_full_path: str,
                                                **kwargs: Dict[str, object]) -> Sequence[object]:
        """
        a modular function of the class. it is meant to support all inheriting classes which will override the
        calc_prediction_error() method only. it expects the same init and overall interface
        as the BaselineCell2CellInfluenceAnalyzer class.
        given a treatment full type (as it is recorded in the metadata file), this function creates an instance of
        an influence analyzer class (e.g., BaselineCell2CellInfluenceAnalyzer) and calculates the error
        of the analyzer for all the experiments under that treatment using 'calc_prediction_error' method.
        :param full_treatment_type: str, the full name of the treatment to analyze (character case sensitive).
        :param meta_data_full_file_path: str, the path the experiments' metadata file.
        :param all_experiments_dir_full_path: str, the path to the directory storing all experiments' csv files.
        :param kwargs: all kwargs have default values. optional kwargs-
            analyzer_class: instance of BaselineCell2CellInfluenceAnalyzer, used to calculate the prediction & error.
            distance_metric_from_true_times_of_death: str, see BaselineCell2CellInfluenceAnalyzer documentation.
            threshold_dist: int, see BaselineCell2CellInfluenceAnalyzer documentation..
            file_name_metadata_col_name: str, the name of the filename column in the metadata file.
            treatment_metadata_col_name: str, the name of the treatment column in the metadata file.
            temporal_resolution_metadata_col_name: str, the name of the temporal resolution column in the metadata file.
        :return: list of error values for all experiments under treatment.
        """

        influence_analyzer = kwargs.get('analyzer_class', BaselineCell2CellInfluenceAnalyzer)
        distance_metric = kwargs.get('distance_metric_from_true_times_of_death', 'rmse')
        influence_threshold_dist = kwargs.get('threshold_dist', DIST_THRESHOLD_IN_PIXELS)
        file_name_col_name = kwargs.get('file_name_metadata_col_name', 'File Name')
        treatment_col_name = kwargs.get('treatment_metadata_col_name', 'Treatment')
        temporal_resolution_col_name = kwargs.get('temporal_resolution_metadata_col_name', 'Time Interval (min)')

        meta_data_df = pd.read_csv(meta_data_full_file_path)
        all_experiments_meta_data_under_treatment = meta_data_df[meta_data_df[treatment_col_name] == full_treatment_type]
        all_experiments_filename_under_treatment = all_experiments_meta_data_under_treatment.loc[:, [file_name_col_name]].values.flatten()
        all_experiments_temporal_resolution_under_treatment = all_experiments_meta_data_under_treatment.loc[:, [temporal_resolution_col_name]].values.flatten()

        exps_errors = list()

        for exp_idx, exp_details in enumerate(zip(all_experiments_filename_under_treatment, all_experiments_temporal_resolution_under_treatment)):
            exp_filename, exp_temporal_res = exp_details[0], exp_details[1]
            exp_file_full_path = os.sep.join([all_experiments_dir_full_path, exp_filename])
            exp_baseline = influence_analyzer(file_full_path=exp_file_full_path,
                                              metadata_file_full_path=meta_data_full_file_path,
                                              threshold_dist=influence_threshold_dist,
                                              distance_metric_from_true_times_of_death=distance_metric)
            exp_error = exp_baseline.calc_prediction_error()
            exps_errors.append(exp_error)

        return exps_errors
    # def visualize_metric(self):
    #     if self._base_line_calculated is not True:
    #         raise RuntimeError(f'baseline results were not calculated, please invoke calc_baseline method')
    #
    #     fig, axis = plt.subplots(1, 2)
    #     axis[0]



if __name__ == '__main__':
    #### single experiment test ####
    single_file_path = ALL_TREATMENT_EXPERIMENTS_DIR + '\\20161129_MCF7_FB_xy11.csv'
    # baseline_influence_analyzer = BaselineCell2CellInfluenceAnalyzer(file_full_path=single_file_path,
    #                                                                  kwargs={'distance_metric_from_true_times_of_death':'kl_divergence'})
    # print(baseline_influence_analyzer.calc_prediction_error())
    #### all experiments in treatment test ####
    # full_treatment_type = 'DMEM+7.5uM erastin'
    # all_experiments_dir_full_path = NON_COMPRESSED_FILE_MAIN_DIR
    # meta_data_full_file_path = '../Data/Experiments_XYT_CSV/ExperimentsMetaData.csv'
    # treatment_results = BaselineCell2CellInfluenceAnalyzer.multiple_experiments_of_treatment_error(full_treatment_type=full_treatment_type,
    #                                                                                                meta_data_full_file_path=meta_data_full_file_path,
    #                                                                                                all_experiments_dir_full_path=all_experiments_dir_full_path)
    # print(treatment_results)



    # df_results = pd.DataFrame(columns=['Baseline Error', 'B', 'C'])
    #
    # for i in range(1,5):
    #     single_file_path = NON_COMPRESSED_FILE_MAIN_DIR + '\\20161129_MCF7_FB_xy11.csv'
    #     baseline_influence_analyzer = BaselineCell2CellInfluenceAnalyzer(file_full_path=single_file_path,
    #                                                                      kwargs={'distance_metric_from_true_times_of_death':'rmse'})
    #     error = baseline_influence_analyzer.calc_prediction_error()
    #     df_results = df_results.append(pd.DataFrame({'Baseline Error': error[0], 'B': i, 'C': i+1}, index=[0]), ignore_index=True)
    #
    #
    # df_results.to_csv('results.csv')



