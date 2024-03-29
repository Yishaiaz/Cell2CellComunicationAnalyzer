import csv

from matplotlib.pyplot import axline

from Pillars.analyzer import *
import networkx as nx
import seaborn as sns
from Pillars.consts import *
import Pillars.consts as consts
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from matplotlib import animation
from matplotlib.pyplot import cm
from matplotlib.animation import PillowWriter

from Pillars.pillar_neighbors import *


def show_last_image_masked(mask_path=None, pillars_mask=None):
    """
    show the mask on the video's last image
    :param mask_path:
    :return:
    """
    last_img = get_last_image()

    plt.imshow(last_img, cmap=plt.cm.gray)
    if Consts.RESULT_FOLDER_PATH is not None:
        plt.savefig(Consts.RESULT_FOLDER_PATH + "/last_image.png")
        plt.close()  # close the figure window

    if Consts.SHOW_GRAPH:
        plt.show()

    if mask_path is not None:
        with open(mask_path, 'rb') as f:
            pillars_mask = np.load(f)
    pillars_mask = 255 - pillars_mask
    mx = ma.masked_array(last_img, pillars_mask)
    plt.imshow(mx, cmap=plt.cm.gray)
    if Consts.RESULT_FOLDER_PATH is not None:
        plt.savefig(Consts.RESULT_FOLDER_PATH + "/mask.png")
        plt.close()  # close the figure window
        print("saved new mask.png")
    if Consts.SHOW_GRAPH:
        # add the centers location on the image
        # centers = find_centers()
        # for center in centers:

        #     s = '(' + str(center[0]) + ',' + str(center[1]) + ')'
        #     plt.text(center[VIDEO_06_LENGTH], center[0], s=s, fontsize=7, color='red')
        plt.show()


def indirect_alive_neighbors_correlation_plot(pillar_location, only_alive=True):
    """
    Plotting the correlation of a pillar with its all indirected neighbors
    :param pillar_location:
    :param only_alive:
    :return:
    """

    my_G = nx.Graph()
    nodes_loc = get_all_center_ids()
    node_loc2index = {}
    for i in range(len(nodes_loc)):
        node_loc2index[nodes_loc[i]] = i
        my_G.add_node(i)

    if only_alive:
        pillars = get_alive_pillars_to_intensities()
    else:
        # pillars = get_pillar_to_intensities(get_images_path())
        pillars = normalized_intensities_by_mean_background_intensity()

    pillar_loc = pillar_location
    indirect_neighbors_dict = get_pillar_indirect_neighbors_dict(pillar_location)
    # alive_pillars = get_alive_pillars_to_intensities()
    directed_neighbors = get_pillar_directed_neighbors(pillar_loc)
    indirect_alive_neighbors = {pillar: indirect_neighbors_dict[pillar] for pillar in pillars.keys() if
                                pillar not in directed_neighbors}
    pillars_corr = get_indirect_neighbors_correlation(pillar_loc, only_alive)
    for no_n1 in indirect_alive_neighbors.keys():
        my_G.add_edge(node_loc2index[pillar_loc], node_loc2index[no_n1])
        try:
            my_G[node_loc2index[pillar_loc]][node_loc2index[no_n1]]['weight'] = pillars_corr[str(pillar_loc)][
                str(no_n1)]
        except:
            x = -1

    edges, weights = zip(*nx.get_edge_attributes(my_G, 'weight').items())

    cmap = plt.cm.seismic
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=-1, vmax=1))
    # pillar2mask = get_last_img_mask_for_each_pillar()
    frame2pillars = get_alive_center_ids_by_frame_v2()  # get_frame_to_alive_pillars_by_same_mask(pillar2mask)

    nodes_loc_y_inverse = [(loc[1], loc[0]) for loc in nodes_loc]
    nx.draw(my_G, nodes_loc_y_inverse, with_labels=True, node_color='gray', edgelist=edges, edge_color=weights,
            width=3.0,
            edge_cmap=cmap)
    plt.colorbar(sm)
    if Consts.SHOW_GRAPH:
        plt.show()


def correlation_plot(only_alive=True,
                     neighbors_str='all',
                     alive_correlation_type='symmetric',
                     pillars_corr_df=None,
                     frame_to_show=None):
    """
    Plotting graph of correlation between neighboring pillars
    Each point represent pillar itop_5_neighboring_corr_animationn its exact position in the image, and the size of each point represent how many
    time frames the pillar was living (the larger the pillar, the sooner he started to live)
    :param only_alive:
    :param neighbors_str:
    :param alive_correlation_type:
    :return:
    """
    my_G = nx.Graph()
    last_img = get_last_image()
    alive_centers = get_seen_centers_for_mask()
    nodes_loc = generate_centers_from_alive_centers(alive_centers, len(last_img))
    if neighbors_str == 'alive2back':
        neighbors = get_alive_pillars_in_edges_to_l1_neighbors()[0]
    elif neighbors_str == 'back2back':
        neighbors = get_background_level_1_to_level_2()
    elif neighbors_str == 'random':
        neighbors = get_random_neighbors()
    else:
        neighbors = get_alive_pillars_to_alive_neighbors()

    node_loc2index = {}
    for i in range(len(nodes_loc)):
        node_loc2index[nodes_loc[i]] = i
        my_G.add_node(i)

    if alive_correlation_type == 'all':
        alive_pillars_correlation = get_alive_pillars_correlation()
    elif alive_correlation_type == 'symmetric':
        alive_pillars_correlation = get_alive_pillars_symmetric_correlation()
    elif alive_correlation_type == 'custom':
        alive_pillars_correlation = pillars_corr_df
    all_pillars_corr = get_all_pillars_correlations()

    if only_alive:
        correlation = alive_pillars_correlation
    else:
        correlation = all_pillars_corr

    for n1 in neighbors.keys():
        for n2 in neighbors[n1]:
            my_G.add_edge(node_loc2index[n1], node_loc2index[n2])
            try:
                my_G[node_loc2index[n1]][node_loc2index[n2]]['weight'] = correlation[str(n1)][str(n2)]
            except:
                x = 1

    edges, weights = zip(*nx.get_edge_attributes(my_G, 'weight').items())
    cmap = plt.cm.seismic
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=-1, vmax=1))
    # pillar2mask = get_last_img_mask_for_each_pillar()
    frame2pillars = get_alive_center_ids_by_frame_v2()  # get_frame_to_alive_pillars_by_same_mask(pillar2mask)
    nodes_loc_y_inverse = [(loc[1], loc[0]) for loc in nodes_loc]
    if frame_to_show:
        img_to_show = get_images(get_images_path())[frame_to_show]
    else:
        img_to_show = get_images(get_images_path())[-1]
    plt.imshow(img_to_show, cmap=plt.cm.gray)

    nx.draw(my_G, nodes_loc_y_inverse, with_labels=False, node_color='black', edgelist=edges, edge_color=weights,
            width=3.0,
            edge_cmap=cmap, node_size=15,
            vmin=-1, vmax=1, edge_vmin=-1, edge_vmax=1)
    plt.colorbar(sm)
    if Consts.SHOW_GRAPH:
        plt.show()
    x = 1


def build_gc_directed_graph(gc_df, non_stationary_pillars=None, inwards=None, outwards=None, random_neighbors=False,
                            draw=True):
    """
    Plotting a directed graph where an arrow represent that the pillar was "granger cause" the other pillar
    :param gc_df: dataframe with granger causality significance values
    :param only_alive:
    :return:
    """
    #
    # if Consts.USE_CACHE and os.path.isfile(Consts.gc_graph_cache_path):
    #     with open(Consts.gc_graph_cache_path, 'rb') as handle:
    #         pillar_to_neighbors = pickle.load(handle)
    #         return pillar_to_neighbors

    my_G = nx.Graph().to_directed()
    nodes_loc = get_all_center_ids()
    # neighbors1, neighbors2 = get_pillar_to_neighbors()
    node_loc2index = {}
    for i in range(len(nodes_loc)):
        node_loc2index[str(nodes_loc[i])] = i
        my_G.add_node(i)
    # alive_pillars_correlation = get_alive_pillars_correlation()
    if random_neighbors:
        neighbors = get_random_neighbors()
    else:
        neighbors = get_alive_pillars_to_alive_neighbors()

    if Consts.only_alive:
        correlation = get_alive_pillars_symmetric_correlation()
    else:
        correlation = get_all_pillars_correlations()

    p_vals_lst = []
    for col in gc_df.keys():
        for row, _ in gc_df.iterrows():
            if eval(row) in neighbors[eval(col)]:
                p_vals_lst.append(gc_df[col][row])
            if gc_df[col][row] < Consts.gc_pvalue_threshold and eval(row) in neighbors[eval(col)]:
                # if edges_direction_lst:
                #     if (col, row) in edges_direction_lst:
                #         my_G.add_edge(node_loc2index[col], node_loc2index[row])
                #         try:
                #             my_G[node_loc2index[col]][node_loc2index[row]]['weight'] = correlation[col][row]
                #         except:
                #             x = 1
                # else:
                my_G.add_edge(node_loc2index[col], node_loc2index[row])
                try:
                    my_G[node_loc2index[col]][node_loc2index[row]]['weight'] = correlation[col][row]
                except:
                    x = 1

    # return my_G, p_vals_lst
    if draw:
        nodes_loc_y_inverse = [(loc[1], loc[0]) for loc in nodes_loc]

        if nx.get_edge_attributes(my_G, 'weight') == {}:
            return

        edges, weights = zip(*nx.get_edge_attributes(my_G, 'weight').items())
        # edges = list(filter(lambda x: x[0] == 52, edges))

        img = get_last_image_whiten(build_image=Consts.build_image)
        fig, ax = plt.subplots()
        ax.imshow(img, cmap='gray')

        if not non_stationary_pillars:
            non_stationary_pillars = []
        if not inwards:
            inwards = []
        if not outwards:
            outwards = []

        node_idx2loc = {v: k for k, v in node_loc2index.items()}

        node_color = []
        for node in my_G.nodes():
            if node_idx2loc[node] in non_stationary_pillars:
                node_color.append('red')
            else:
                node_color.append('black')

        edge_color = []
        for edge in my_G.edges():
            e = (node_idx2loc[edge[0]], node_idx2loc[edge[1]])
            if e in inwards:
                edge_color.append('green')
            elif e in outwards:
                edge_color.append('blue')
            else:
                edge_color.append('gray')

        node_size = [20 if c == 'red' else 1 for c in node_color]

        nx.draw(my_G, nodes_loc_y_inverse, node_color=node_color, edgelist=edges, edge_color=edge_color,
                width=3.0,
                node_size=node_size)
        nx.draw_networkx_labels(my_G, nodes_loc_y_inverse, font_color="whitesmoke", font_size=8)

        # plt.scatter(get_image_size()[0]/2, get_image_size()[1]/2, s=250, c="red")

        # ax.plot()
        if Consts.RESULT_FOLDER_PATH is not None:
            plt.savefig(Consts.RESULT_FOLDER_PATH + "/gc.png")
            plt.close()  # close the figure window
            print("saved gc.png")
        if Consts.SHOW_GRAPH:
            plt.show()
        x = 1


# TODO: delete
def build_gc_directed_graph_test(gc_df, non_stationary_pillars=None, inwards=None, outwards=None, only_alive=True,
                                 draw=True):
    """
    Plotting a directed graph where an arrow represent that the pillar was "granger cause" the other pillar
    :param gc_df: dataframe with granger causality significance values
    :param only_alive:
    :return:
    """
    my_G = nx.Graph().to_directed()
    nodes_loc = get_all_center_ids()
    # neighbors1, neighbors2 = get_pillar_to_neighbors()
    node_loc2index = {}
    for frame in range(len(nodes_loc)):
        node_loc2index[str(nodes_loc[frame])] = frame
        my_G.add_node(frame)
    # alive_pillars_correlation = get_alive_pillars_correlation()
    alive_pillars_correlation = get_alive_pillars_symmetric_correlation()
    all_pillars_corr = get_all_pillars_correlations()
    neighbors = get_alive_pillars_to_alive_neighbors()

    if only_alive:
        correlation = alive_pillars_correlation
    else:
        correlation = all_pillars_corr

    for col in gc_df.keys():
        for row, _ in gc_df.iterrows():
            if gc_df[col][row] < Consts.gc_pvalue_threshold and eval(row) in neighbors[eval(col)]:
                my_G.add_edge(node_loc2index[col], node_loc2index[row])
                try:
                    my_G[node_loc2index[col]][node_loc2index[row]]['weight'] = correlation[col][row]
                except:
                    x = 1

    if draw:
        cmap = plt.cm.seismic
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=-1, vmax=1))
        # plt.colorbar(sm)

        # pillar2mask = get_last_img_mask_for_each_pillar()
        frame2alive_pillars = get_alive_center_ids_by_frame_v2()  # get_frame_to_alive_pillars_by_same_mask(pillar2mask)
        nodes_loc_y_inverse = [(loc[1], loc[0]) for loc in nodes_loc]

        edges, weights = zip(*nx.get_edge_attributes(my_G, 'weight').items())
        # edges = list(filter(lambda x: x[0] == 52, edges))

        img = get_last_image_whiten(build_image=Consts.build_image)
        fig, ax = plt.subplots()
        ax.imshow(img, cmap='gray')

        if not non_stationary_pillars:
            non_stationary_pillars = []
        if not inwards:
            inwards = []
        if not outwards:
            outwards = []

        node_idx2loc = {v: k for k, v in node_loc2index.items()}

        node_color = []
        for node in my_G.nodes():
            if node_idx2loc[node] in non_stationary_pillars:
                node_color.append('red')
            else:
                node_color.append('black')

        edge_color = []
        for edge in my_G.edges():
            e = (node_idx2loc[edge[0]], node_idx2loc[edge[1]])
            if e in inwards:
                edge_color.append('green')
            elif e in outwards:
                edge_color.append('blue')
            else:
                edge_color.append('gray')

        node_size = [20 if c == 'red' else 1 for c in node_color]

        nx.draw(my_G, nodes_loc_y_inverse, with_labels=True, node_color=node_color, edgelist=edges,
                edge_color=edge_color,
                width=3.0,
                node_size=node_size)
        nx.draw_networkx_labels(my_G, nodes_loc_y_inverse, font_color="whitesmoke")

        # ax.plot()
        if Consts.SHOW_GRAPH:
            plt.show()
        x = 1
    return my_G


def correlation_histogram(correlations_df):
    """
    Plotting a histogram of the pillars correlations
    :param correlations_df:
    :return:
    """
    corr = set()
    correlations = correlations_df
    for i in correlations:
        for j in correlations:
            if i != j:
                corr.add(correlations[i][j])
    corr_array = np.array(list(corr))
    mean_corr = np.mean(corr_array)
    sns.histplot(data=corr_array, kde=True)
    plt.xlabel("Correlation")
    if Consts.SHOW_GRAPH:
        plt.show()
    mean_corr = format(mean_corr, ".3f")
    print("mean correlations: " + str(mean_corr))
    return mean_corr


def neighbors_correlation_histogram(correlations_lst, neighbors_dict):
    """
    Display histogram plot of the correlations between the neighbors
    :param correlations_df:
    :param neighbors_dict:
    :param symmetric_corr:
    :return:
    """
    sns.distplot(a=correlations_lst, kde=True)
    plt.xlim(-1, 1)
    plt.title("Correlation of Neighbors Pillars")
    plt.xlabel("Correlation")
    if Consts.RESULT_FOLDER_PATH is not None:
        plt.savefig(Consts.RESULT_FOLDER_PATH + "/neighbors_corr_histogram.png")
        plt.close()  # close the figure window
    print("neighbors mean correlation: " + str(np.nanmean(correlations_lst)))
    if Consts.SHOW_GRAPH:
        plt.show()


def non_neighbors_correlation_histogram(correlations_lst, neighbors_dict):
    sns.distplot(a=correlations_lst, kde=True)
    plt.xlim(-1, 1)
    plt.title("Correlation of Non-Neighbors Pillars")
    plt.xlabel("Correlation")
    if Consts.RESULT_FOLDER_PATH is not None:
        plt.savefig(Consts.RESULT_FOLDER_PATH + "/non_neighbors_corr_histogram.png")
        plt.close()  # close the figure window
    print("non-neighbors mean correlation: " + str(np.nanmean(correlations_lst)))
    if Consts.SHOW_GRAPH:
        plt.show()


def plot_pillar_time_series():
    """
    Plotting a time series graph of the pillar intensity over time
    :return:
    """
    if Consts.normalized:
        pillar2intens = normalized_intensities_by_mean_background_intensity()
    else:
        pillar2intens = get_pillar_to_intensities(get_images_path())

    # for p in pillar2intens.keys():

    intensities_1 = pillar2intens[(524, 523)]
    intensities_2 = pillar2intens[(454, 493)]
    intensities_3 = pillar2intens[(463, 569)]
    x = [i * 19.94 for i in range(len(intensities_1))]
    intensities_1 = [i * 0.0519938 for i in intensities_1]
    intensities_2 = [i * 0.0519938 for i in intensities_2]
    intensities_3 = [i * 0.0519938 for i in intensities_3]
    plt.plot(x, intensities_1, label='(524, 523)')
    plt.plot(x, intensities_2, label='(454, 493)')
    plt.plot(x, intensities_3, label='(463, 569)')

    # plt.plot(x, intensities)
    plt.xlabel('Time (sec)')
    plt.ylabel('Intensity (micron)')
    # plt.title('Pillar ' + str(pillar_loc))
    plt.legend()
    if Consts.SHOW_GRAPH:
        plt.show()


def compare_neighbors_corr_histogram_random_vs_real(random_amount):
    """
    Show on same plot the mean correlation of the real neighbors and
    :param random_amount:
    :return:
    """
    mean_original_nbrs, _ = get_neighbors_avg_correlation(get_alive_pillars_symmetric_correlation(),
                                                          get_alive_pillars_to_alive_neighbors())
    means = []
    rand = []
    for i in range(random_amount):
        mean_random_nbrs = get_neighbors_avg_correlation(get_alive_pillars_symmetric_correlation(),
                                                         get_random_neighbors())
        means.append(mean_random_nbrs)
        rand.append('random' + str(i + 1))
    print("Random nbrs mean correlation: " + str(np.mean(means)))
    means.append(mean_original_nbrs)
    rand.append('original')
    fig, ax = plt.subplots()
    ax.scatter(rand, means)
    plt.ylabel('Average Correlation')
    plt.xticks(rotation=45)
    if Consts.RESULT_FOLDER_PATH is not None:
        plt.savefig(Consts.RESULT_FOLDER_PATH + "/neighbors_corr_histogram_random_vs_real.png")
        plt.close()  # close the figure window
        print("saved neighbors_corr_histogram_random_vs_real.png")
    if Consts.SHOW_GRAPH:
        plt.show()


def edges_distribution_plots(gc_df, pillar_intensity_dict=None):
    alive_pillars_correlation = get_alive_pillars_symmetric_correlation()
    neighbors = get_alive_pillars_to_alive_neighbors()
    no_edge = []
    one_sided_edge = []
    two_sided_edge = []

    rows = list(gc_df.keys())
    for i, col in enumerate(gc_df.keys()):
        for j in range(i + 1, len(rows)):
            row = rows[j]
            if eval(row) in neighbors[eval(col)]:
                if pillar_intensity_dict:
                    corr = pearsonr(pillar_intensity_dict[col], pillar_intensity_dict[row])[0]
                else:
                    corr = alive_pillars_correlation[col][row]
                if gc_df[col][row] < 0.05 and gc_df[row][col] < 0.05:
                    two_sided_edge.append(corr)
                elif (gc_df[col][row] < 0.05 and gc_df[row][col] > 0.05) or (
                        gc_df[col][row] > 0.05 and gc_df[row][col] < 0.05):
                    one_sided_edge.append(corr)
                else:
                    no_edge.append(corr)

    # for col in gc_df.keys():
    #     for row, _ in gc_df.iterrows():
    #         if eval(row) in neighbors[eval(col)]:
    #             if pillar_intensity_dict:
    #                 corr = pearsonr(pillar_intensity_dict[col], pillar_intensity_dict[row])[0]
    #             else:
    #                 corr = alive_pillars_correlation[col][row]
    #             if gc_df[col][row] < 0.05 and gc_df[row][col] < 0.05:
    #                 two_sided_edge.append(corr)
    #             elif (gc_df[col][row] < 0.05 and gc_df[row][col] > 0.05) or (
    #                     gc_df[col][row] > 0.05 and gc_df[row][col] < 0.05):
    #                 one_sided_edge.append(corr)
    #             else:
    #                 no_edge.append(corr)
    sns.histplot(data=no_edge, kde=True)
    plt.xlabel("Correlations")
    plt.title('Correlation of no edges between neighbors')
    if Consts.SHOW_GRAPH:
        plt.show()
    print("number of neighbors with no edges: " + str(len(no_edge)))
    print("average of neighbors with no edges: " + str(np.mean(no_edge)))
    sns.histplot(data=one_sided_edge, kde=True)
    plt.xlabel("Correlations")
    plt.title('Correlation of 1 sided edges between neighbors')
    if Consts.SHOW_GRAPH:
        plt.show()
    print("number of neighbors with 1 edge: " + str(len(one_sided_edge)))
    print("average of neighbors with 1 edge: " + str(np.mean(one_sided_edge)))
    sns.histplot(data=two_sided_edge, kde=True)
    plt.xlabel("Correlations")
    plt.title('Correlation of 2 sided edges between neighbors')
    if Consts.SHOW_GRAPH:
        plt.show()
    print("number of neighbors with 2 edges: " + str(len(two_sided_edge)))
    print("average of neighbors with 2 edges: " + str(np.mean(two_sided_edge)))


def in_out_degree_distribution(in_degree_list, out_degree_list):
    sns.histplot(data=in_degree_list, kde=True)
    plt.xlabel("In Degree")
    plt.title('Pillars In Degree Distribution')
    if Consts.SHOW_GRAPH:
        plt.show()
    print("In degree average: " + str(np.mean(in_degree_list)))
    sns.histplot(data=out_degree_list, kde=True)
    plt.xlabel("Out Degree")
    plt.title('Pillars Out Degree Distribution')
    if Consts.SHOW_GRAPH:
        plt.show()
    print("Out degree average: " + str(np.mean(out_degree_list)))


def features_correlations_heatmap(output_path_type, custom_df=None):
    if custom_df is None:
        output_df = get_output_df(output_path_type)
    else:
        output_df = custom_df
    f, ax = plt.subplots(figsize=(10, 8))
    corr = output_df.corr()
    sns.heatmap(corr, mask=np.zeros_like(corr, dtype=np.bool), annot=True,
                cmap=sns.diverging_palette(220, 10, as_cmap=True),
                square=True, ax=ax)
    ax.tick_params(axis='x', rotation=45)
    ax.tick_params(axis='y', rotation=45)
    if Consts.SHOW_GRAPH:
        plt.show()


def pca_number_of_components(output_path_type, custom_df=None):
    # get the number of components to pca - a rule of thumb is to preserve around 80 % of the variance
    if custom_df is None:
        output_df = get_output_df(output_path_type)
    else:
        output_df = custom_df
    x = StandardScaler().fit_transform(output_df)
    pca = PCA()
    pca.fit(x)
    plt.figure(figsize=(10, 8))
    plt.title('Explained Variance by Components')
    plt.xlabel('Number of Components')
    plt.ylabel('Cumulative Explained Variance')
    plt.plot(range(1, output_df.shape[1] + 1), pca.explained_variance_ratio_.cumsum(), marker='o', linestyle='--')
    if Consts.SHOW_GRAPH:
        plt.show()


def plot_2d_pca_components(targets_list, output_path_type, n_components, custom_df=None):
    # plot 2D pca of all components in one plot
    pca, principal_components = get_pca(output_path_type, n_components=n_components, custom_df=custom_df)
    labels = {
        str(i): f"PC {i + 1} ({var:.1f}%)"
        for i, var in enumerate(pca.explained_variance_ratio_ * 100)
    }
    fig = px.scatter_matrix(
        principal_components,
        labels=labels,
        dimensions=range(principal_components.shape[1]),
        color=targets_list
    )
    fig.update_traces(diagonal_visible=False)
    fig.show()


def components_feature_weight(pca):
    # Components Feature Weight
    if len(pca.components_) == 2:
        subplot_titles = ("PC1", "PC2")
        cols = 2
    if len(pca.components_) == 3:
        subplot_titles = ("PC1", "PC2", "PC3")
        cols = 3
    if len(pca.components_) == 4:
        subplot_titles = ("PC1", "PC2", "PC3", "PC4")
        cols = 4
    fig = make_subplots(rows=1, cols=cols, subplot_titles=subplot_titles)
    fig.add_trace(
        go.Scatter(y=pca.components_[0], mode='markers'),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(y=pca.components_[1], mode='markers'),
        row=1, col=2
    )
    if len(pca.components_) == 3:
        fig.add_trace(
            go.Scatter(y=pca.components_[2], mode='markers'),
            row=1, col=3
        )
    if len(pca.components_) == 4:
        fig.add_trace(
            go.Scatter(y=pca.components_[2], mode='markers'),
            row=1, col=3
        )
        fig.add_trace(
            go.Scatter(y=pca.components_[3], mode='markers'),
            row=1, col=4
        )
    fig.update_xaxes(title_text="Feature", row=1, col=2)
    fig.update_yaxes(title_text="Weight", row=1, col=1)
    fig.show()


def features_coefficient_heatmap(pca, output_path_type, custom_df=None):
    if custom_df is None:
        output_df = get_output_df(output_path_type)
    else:
        output_df = custom_df
    for i in range(len(pca.components_)):
        ax = sns.heatmap(pca.components_[i].reshape(1, output_df.shape[1]),
                         cmap='seismic',
                         yticklabels=["PC" + str(i + 1)],
                         xticklabels=list(output_df.columns),
                         cbar_kws={"orientation": "horizontal"},
                         annot=True, vmin=-1, vmax=1)
        ax.set_aspect("equal")
        ax.tick_params(axis='x', rotation=20)
        sns.set(rc={"figure.figsize": (3, 3)})
        if Consts.SHOW_GRAPH:
            plt.show()


def gc_edge_probability_original_vs_random(gc_df, gc_edge_prob_lst):
    fig, ax = plt.subplots()
    original = probability_for_gc_edge(gc_df, random_neighbors=False)
    ax.scatter(0, np.mean(gc_edge_prob_lst), label="random")
    ax.scatter(1, original, label="original")
    plt.ylabel("Edge Probability")
    plt.title("GC Edge Probability - Original vs. Random Neighbors")
    ax.legend()
    if Consts.RESULT_FOLDER_PATH is not None:
        plt.savefig(Consts.RESULT_FOLDER_PATH + "/gc_probability_original_vs_random.png")
        plt.close()  # close the figure window
        print("saved gc_probability_original_vs_random.png")
    if Consts.SHOW_GRAPH:
        plt.show()


# decide on the number of clustering to k-means. wcss = Within Cluster Sum of Squares
def number_clusters_kmeans(principalComponents):
    global kmeans_pca
    wcss = []
    for i in range(1, 9):
        kmeans_pca = KMeans(n_clusters=i, init='k-means++', random_state=42)
        kmeans_pca.fit(principalComponents)
        wcss.append(kmeans_pca.inertia_)
    plt.figure(figsize=(10, 8))
    plt.title('K-means with PCA Clusters')
    plt.xlabel('Number of Clusters')
    plt.ylabel('WCSS')
    plt.plot(range(1, 9), wcss, marker='o', linestyle='--')
    if Consts.SHOW_GRAPH:
        plt.show()


# implement k-means with pca
def k_means(principalComponents, output_path_type, n_clusters=2, custom_df=None):
    global kmeans_pca
    kmeans_pca = KMeans(n_clusters=n_clusters, init='k-means++', random_state=42)
    kmeans_pca.fit(principalComponents)
    if custom_df is None:
        output_df = get_output_df(output_path_type)
    else:
        output_df = custom_df
    df_segm_pca_kmeans = pd.concat([output_df.reset_index(drop=True), pd.DataFrame(principalComponents)], axis=1)
    n_components = principalComponents.shape[1]
    df_segm_pca_kmeans.columns.values[-n_components:] = ['Component ' + str(i + 1) for i in range(n_components)]
    df_segm_pca_kmeans['Segment K-means PCA'] = kmeans_pca.labels_
    df_segm_pca_kmeans['Segment'] = df_segm_pca_kmeans['Segment K-means PCA'].map({0: 'first', 1: 'second'})
    for i in range(n_components):
        x_axis = df_segm_pca_kmeans['Component ' + str(i + 1)]
        for j in range(i + 1, n_components):
            y_axis = df_segm_pca_kmeans['Component ' + str(j + 1)]
            plt.figure(figsize=(10, 8))
            sns.scatterplot(x_axis, y_axis, hue=df_segm_pca_kmeans['Segment'], palette=['g', 'r'])
            plt.title('Clusters by PCA Components')
            if Consts.SHOW_GRAPH:
                plt.show()


def plot_average_correlation_neighbors_vs_non_neighbors(lst1, lst2, labels=None, title=None, xlabel=None,
                                                        ylabel=None, special_marker=None):
    f, ax = plt.subplots(figsize=(6, 6))
    color = iter(cm.rainbow(np.linspace(0, 1, len(labels))))
    for i in range(len(lst1)):
        c = next(color)
        marker = 'bo'
        if special_marker:
            marker = "*" if special_marker[i] == 'special' else '.'
        plt.plot(float(lst2[i]), float(lst1[i]), marker, label=labels[i], c=c)

    # plt.axis('square')
    plt.setp(ax, xlim=(-1, 1), ylim=(-1, 1))
    axline([ax.get_xlim()[0], ax.get_ylim()[0]], [ax.get_xlim()[1], ax.get_ylim()[1]], ls='--')
    if title:
        plt.title(title)
    else:
        plt.title('Average Correlation', fontsize=15)
    if xlabel:
        plt.xlabel(xlabel, fontsize=12)
    else:
        plt.xlabel('Non-Neighbor pair correlation')
    if ylabel:
        plt.ylabel(ylabel, fontsize=12)
    else:
        plt.ylabel('Neighbor pair correlation')
    if labels is not None:
        plt.legend(labels)
    if Consts.SHOW_GRAPH:
        plt.show()


def plot_pillar_pairs_correlation_frames_window(pairs_corr_dict, neighbor_pairs=True):
    pairs = []
    n = len(pairs_corr_dict)
    plt.clf()
    for pair, corrs in pairs_corr_dict.items():
        window_num = [n for n in range(1, len(corrs) + 1)]
        plt.plot(window_num, corrs)
        pairs.append(pair)
    plt.xlabel('Window')
    plt.ylabel('Correlation')
    if neighbor_pairs:
        plt.title('Window Correlation - neighbor pairs')
    else:
        plt.title('Window Correlation')
    plt.legend(pairs)

    if Consts.RESULT_FOLDER_PATH is not None:
        if neighbor_pairs:
            plt.savefig(Consts.RESULT_FOLDER_PATH + "/pillar_neighboring_top_" + str(
                n) + "_pairs_correlation_frames_window.png")
            plt.close()  # close the figure window
        else:
            plt.savefig(Consts.RESULT_FOLDER_PATH + "/pillar_top_" + str(n) + "_pairs_correlation_frames_window.png")
            plt.close()  # close the figure window

    if Consts.SHOW_GRAPH:
        plt.show()


def show_correlated_pairs_in_video(n=5, neighbor_pairs=True):
    pairs_corr_dict = get_top_pairs_corr_in_each_frames_window(n=n, neighbor_pairs=neighbor_pairs)
    all_images = get_images(get_images_path())

    fig = plt.figure()
    ax = fig.add_subplot()

    coords = []

    for pair in pairs_corr_dict.keys():
        coordinate_1 = eval(pair[0])
        coordinate_2 = eval(pair[1])
        coords.append([coordinate_1, coordinate_2])

    def animate(i):
        ax.clear()

        color = iter(cm.rainbow(np.linspace(0, 1, len(pairs_corr_dict.keys()))))

        for pair in pairs_corr_dict.keys():
            coordinate_1 = eval(pair[0])
            coordinate_2 = eval(pair[1])
            c = next(color)
            ax.plot([coordinate_1[1], coordinate_2[1]], [coordinate_1[0], coordinate_2[0]], c=c, linewidth=1)
        ax.legend(coords)

        ax.imshow(all_images[i % len(all_images)], cmap=plt.cm.gray)

    ani = animation.FuncAnimation(fig, animate, frames=len(all_images), interval=50)

    if Consts.RESULT_FOLDER_PATH is not None:
        writergif = animation.PillowWriter(fps=30)
        if neighbor_pairs:
            ani.save(Consts.RESULT_FOLDER_PATH + "/top_" + str(n) + "_neighboring_corr_animation.gif", dpi=300,
                     writer=writergif)
            plt.close()  # close the figure window
        else:
            ani.save(Consts.RESULT_FOLDER_PATH + "/top_" + str(n) + "_corr_animation.gif", dpi=300, writer=writergif)
            plt.close()  # close the figure window

    if Consts.SHOW_GRAPH:
        plt.show()


def show_correlated_pairs_in_last_image(n=5, neighbor_pairs=True):
    plt.clf()
    pairs_corr_dict = get_top_pairs_corr_in_each_frames_window(n=n, neighbor_pairs=neighbor_pairs)
    last_img = get_last_image()
    coords = []

    color = iter(cm.rainbow(np.linspace(0, 1, len(pairs_corr_dict.keys()))))

    for pair in pairs_corr_dict.keys():
        coordinate_1 = eval(pair[0])
        coordinate_2 = eval(pair[1])
        coords.append([coordinate_1, coordinate_2])
        c = next(color)
        plt.plot([coordinate_1[1], coordinate_2[1]], [coordinate_1[0], coordinate_2[0]], c=c, linewidth=1)
    plt.legend(coords)
    plt.imshow(last_img, cmap=plt.cm.gray)

    if Consts.RESULT_FOLDER_PATH is not None:
        if neighbor_pairs:
            plt.savefig(Consts.RESULT_FOLDER_PATH + "/top_" + str(n) + "_correlated_neighboring_pairs_last_image.png")
            plt.close()  # close the figure window
        else:
            plt.savefig(Consts.RESULT_FOLDER_PATH + "/top_" + str(n) + "_correlated_pairs_last_image.png")
            plt.close()  # close the figure window

    if Consts.SHOW_GRAPH:
        plt.show()


def plot_pillar_intensity_with_movement():
    centers_movements = get_alive_centers_movements()
    pillars_intens = get_alive_pillars_to_intensities()
    for pillar, moves in centers_movements.items():
        pillar_id = min(pillars_intens.keys(), key=lambda point: math.hypot(point[1] - pillar[1], point[0] - pillar[0]))
        pillar_movment = []
        for move in moves:
            pillar_movment.append(move['distance'])

        pillar_intens = pillars_intens[pillar_id]
        norm_intens = (pillar_intens - np.min(pillar_intens)) / (np.max(pillar_intens) - np.min(pillar_intens))
        plt.plot(norm_intens, label='intensity')
        plt.plot(pillar_movment, label='movement')
        plt.title('pillar ' + str(pillar_id))
        plt.legend()

        # Consts.RESULT_FOLDER_PATH = "../multi_config_runner_results/13.2/06/movement_intensity_plots"
        # Path(Consts.RESULT_FOLDER_PATH).mkdir(parents=True, exist_ok=True)
        # plt.savefig(Consts.RESULT_FOLDER_PATH + "/movement_intensity_pillar_" + str(pillar_id) + ".png")
        # plt.close()  # close the figure window
        if Consts.SHOW_GRAPH:
            plt.show()


def plot_pillars_intensity_movement_correlations(pillars_intensity_movement_correlations_lst):
    plt.scatter()


def plot_pair_of_pillars_movement_corr_and_intensity_corr(movement_corr_df, intensity_corr_df, neighbors_only=False):
    pillars = movement_corr_df.columns
    neighbors_dict = get_alive_pillars_to_alive_neighbors()

    for p1 in pillars:
        for p2 in pillars:
            if p1 == p2:
                continue
            if neighbors_only:
                if eval(p1) not in neighbors_dict[eval(p2)]:
                    continue
            move_corr = movement_corr_df[p1][p2]
            intens_corr = intensity_corr_df[p1][p2]
            if eval(p1) in neighbors_dict[eval(p2)]:
                plt.scatter(intens_corr, move_corr, c='red', alpha=0.2)
            else:
                plt.scatter(intens_corr, move_corr, c='blue', alpha=0.2)
    plt.xlim(-1, 1)
    plt.ylim(-1, 1)
    plt.xlabel("Intensity correlation")
    plt.ylabel("Movement correlation")
    plt.title("Intensity and Movement Correlation of Pillar Pairs")

    if Consts.RESULT_FOLDER_PATH is not None:
        plt.savefig(Consts.RESULT_FOLDER_PATH + "/intensity_movement_pairs_correlation.png")
        plt.close()  # close the figure window
        print("saved intensity_movement_pairs_correlation.png")

    if Consts.SHOW_GRAPH:
        plt.show()


def plot_pillars_average_intensity_by_movement():
    avg_intens_by_distance = get_average_intensity_by_distance()
    f, ax = plt.subplots(figsize=(6, 6))
    zero = []
    not_zero = []
    for p, intens in avg_intens_by_distance.items():
        intens_dist_zero = intens['avg_intens_when_dist_zero']
        intens_dist_non_zero = intens['avg_intens_when_dist_non_zero']
        # plt.scatter(intens_dist_zero, intens_dist_non_zero)
        zero.append(intens_dist_zero)
        not_zero.append(intens_dist_non_zero)
    plt.scatter(zero, not_zero)

    zero_intens_lst = [d['avg_intens_when_dist_zero'] for d in list(avg_intens_by_distance.values())]
    non_zero_intens_lst = [d['avg_intens_when_dist_non_zero'] for d in list(avg_intens_by_distance.values())]
    min_axis_val = min(min(zero_intens_lst), min(non_zero_intens_lst))
    max_axis_val = max(max(zero_intens_lst), max(non_zero_intens_lst))
    plt.xlabel("Avg intensity when distance == 0")
    plt.ylabel("Avg intensity when distance != 0")
    plt.title("Pillars intensity by movement")
    plt.xlim(min_axis_val, max_axis_val)
    plt.ylim(min_axis_val, max_axis_val)
    axline([ax.get_xlim()[0], ax.get_ylim()[0]], [ax.get_xlim()[1], ax.get_ylim()[1]], ls='--')

    if Consts.RESULT_FOLDER_PATH is not None:
        plt.savefig(Consts.RESULT_FOLDER_PATH + "/Pillars intensity by movement.png")
        plt.close()  # close the figure window

    if Consts.SHOW_GRAPH:
        plt.show()


def plot_average_intensity_by_distance():
    avg_intens_to_dict = get_average_intensity_by_distance()
    f, ax = plt.subplots(figsize=(6, 6))
    all_distances = []
    [all_distances.extend(list(p_dists.keys())) for p_dists in list(avg_intens_to_dict.values())]
    unique_distances = sorted(list(set(all_distances)))

    dist_to_overall_avg_intens = {}
    for dist in unique_distances:
        avg_intens_of_dist = []
        for val in avg_intens_to_dict.values():
            if dist in val:
                avg_intens_of_dist.append(val[dist])
        dist_to_overall_avg_intens[dist] = np.mean(avg_intens_of_dist)

    plt.scatter(dist_to_overall_avg_intens.keys(), dist_to_overall_avg_intens.values())
    plt.xlabel("Distance")
    plt.ylabel("Avg intensity")
    plt.title("Average Intensity By Distance")

    if Consts.RESULT_FOLDER_PATH is not None:
        plt.savefig(Consts.RESULT_FOLDER_PATH + "/Average intensity by distance.png")
        plt.close()  # close the figure window

    if Consts.SHOW_GRAPH:
        plt.show()


def show_peripheral_pillars_in_video(frame_to_peripheral_center_dict):
    frame_to_peripheral_center_dict = frame_to_peripheral_center_dict
    all_images = get_images(get_images_path())

    fig = plt.figure()
    ax = fig.add_subplot()

    def animate(i):
        ax.clear()

        curr_frame = list(frame_to_peripheral_center_dict.keys())[i]
        periph_pillars = frame_to_peripheral_center_dict[curr_frame]["peripherals"]

        y = [p[0] for p in periph_pillars]
        x = [p[1] for p in periph_pillars]
        scatter_size = [3 for center in periph_pillars]

        ax.scatter(x, y, s=scatter_size, color='blue')

        central_pillars = frame_to_peripheral_center_dict[curr_frame]["centrals"]

        y = [p[0] for p in central_pillars]
        x = [p[1] for p in central_pillars]
        scatter_size = [3 for center in central_pillars]

        ax.scatter(x, y, s=scatter_size, color='red')

        ax.imshow(all_images[i % len(all_images)], cmap=plt.cm.gray)

    ani = animation.FuncAnimation(fig, animate, frames=len(all_images), interval=100)
    # Writer = animation.writers['ffmpeg']
    # writer = Writer(fps=20, metadata=dict(artist='Me'), bitrate=1800)
    # writer = animation.FFMpegWriter(fps=10)

    writer = animation.PillowWriter(fps=10000)

    # if Consts.RESULT_FOLDER_PATH is not None:
    #     ani.save(Consts.RESULT_FOLDER_PATH + "/peripheral_pillars.gif", dpi=300, writer=writer)
    #     plt.close()  # close the figure window

    if Consts.SHOW_GRAPH:
        plt.show()


def plot_average_movement_signal_sync_peripheral_vs_central(central_lst, peripheral_lst, labels=None, title=None):
    f, ax = plt.subplots(figsize=(6, 6))
    color = iter(cm.rainbow(np.linspace(0, 1, len(labels))))
    for i in range(len(peripheral_lst)):
        c = next(color)
        plt.plot(central_lst[i], peripheral_lst[i], 'bo', label=labels[i], c=c)

    # plt.axis('square')
    plt.setp(ax, xlim=(-1, 1), ylim=(-1, 1))
    axline([ax.get_xlim()[0], ax.get_ylim()[0]], [ax.get_xlim()[1], ax.get_ylim()[1]], ls='--')
    if title:
        plt.title('Average Movement-Signal Correlation' + ' ' + title)
    else:
        plt.title('Average Correlation')
    plt.ylabel('Peripheral pillars correlation')
    plt.xlabel('Central pillars correlation')
    if labels is not None:
        plt.legend(labels)
    if Consts.SHOW_GRAPH:
        plt.show()


def plot_avg_correlation_spreading_level(exp_type_name, avg_corr, spreading_level):
    f, ax = plt.subplots()
    colors = []
    labels = []
    for i in range(len(exp_type_name)):
        c = 'red' if spreading_level[i] == 'high' else 'blue'
        colors.append(c)
        labels.append(spreading_level[i])
        ax.scatter(exp_type_name[i], float(avg_corr[i][0]), c=c, label=spreading_level[i])

    ax.legend(['high', 'low'])
    plt.xlabel("Experiment")
    plt.ylabel("Avg Correlation")
    plt.title("Experiment Avg Correlation in Spreading Level")

    plt.show()


def plot_experiment_features_heatmap(exp_lst, features_lst, matrix_values):
    matrix_df = pd.DataFrame(matrix_values, columns=features_lst, index=exp_lst)
    plt.figure(figsize=(10, 10))
    sns.set(font_scale=1)

    sns.heatmap(matrix_df,
                annot=True,
                # vmin=-1,
                # vmax=1,
                annot_kws={"fontsize": 9})

    plt.xticks(rotation=15, fontsize=8)
    plt.yticks(rotation=45)

    plt.xlabel('Feature', fontsize=18)
    plt.ylabel('Experiment', fontsize=18)

    plt.show()


def plot_nbrs_correlations_heatmap(correlations_df, neighbors_dict):
    # matrix_df = pd.DataFrame(None, columns=correlations_df.columns, index=correlations_df.columns, dtype='float64')
    labels = correlations_df.applymap(lambda v: '')

    for p, nbrs in neighbors_dict.items():
        for n in nbrs:
            labels.loc[str(p), str(n)] = round(correlations_df.loc[str(p), str(n)], 2)


    sns.heatmap(correlations_df,
                annot=labels,
                mask=correlations_df.isnull(),
                vmin=-1,
                vmax=1,
                annot_kws={"fontsize": 6}, fmt='')

    plt.xticks(rotation=25)
    plt.xlabel('Pillar', fontsize=15)
    plt.ylabel('Pillar', fontsize=15)

    plt.show()


def show_nbrs_distance_graph(nbrs_dict, pillar2middle_img_steps):
    my_G = nx.Graph()

    nodes_loc = list(nbrs_dict)

    node_loc2index = {}
    for i in range(len(nodes_loc)):
        node_loc2index[nodes_loc[i]] = i
        my_G.add_node(i)

    for n1, nbrs in nbrs_dict.items():
        for n2 in nbrs:
            my_G.add_edge(node_loc2index[n1], node_loc2index[n2])
            try:
                my_G[node_loc2index[n1]][node_loc2index[n2]]['weight'] = find_vertex_distance_from_center(n1, n2,
                                                                                                          pillar2middle_img_steps)
            except:
                x = 1

    edges, weights = zip(*nx.get_edge_attributes(my_G, 'weight').items())
    cmap = plt.cm.hot

    max_value = max(pillar2middle_img_steps.values())
    min_value = min(pillar2middle_img_steps.values())

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=min_value, vmax=max_value))
    nodes_loc_y_inverse = [(loc[1], loc[0]) for loc in nodes_loc]
    plt.imshow(get_last_image(), cmap=plt.cm.gray)

    nx.draw(my_G, nodes_loc_y_inverse, with_labels=False, node_color='black', edgelist=edges, edge_color=weights,
            width=3.0,
            edge_cmap=cmap, node_size=15,
            vmin=min_value, vmax=max_value, edge_vmin=min_value, edge_vmax=max_value)
    plt.colorbar(sm)
    plt.show()


def plot_correlation_by_distance_from_center_cell(list_of_dist_to_corr_dict, labels):
    f, ax = plt.subplots(figsize=(6, 6))
    color = iter(cm.rainbow(np.linspace(0, 1, len(labels))))
    for i in range(len(labels)):
        c = next(color)
        dist_to_corr = list_of_dist_to_corr_dict[i]
        plt.plot(list(dist_to_corr.keys()), list(dist_to_corr.values()), label=labels[i], color=c, linestyle='--', marker='o')

    plt.title('Local Correlation by Distance Level From the Cell Center', fontsize=14)
    plt.ylabel('Correlation', fontsize=12)
    plt.xlabel('Distance from cell center', fontsize=12)
    if labels is not None:
        plt.legend(labels)
    if Consts.SHOW_GRAPH:
        plt.show()


