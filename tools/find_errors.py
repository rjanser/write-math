#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Find raw_datasets which are not accepted by the administrator and look
different than other known datasets with the same accepted_formula_id.

(So: Find outliers)
"""
import sys
import logging
logging.basicConfig(level=logging.INFO,
                    stream=sys.stdout,
                    format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Database stuff
import pymysql
import pymysql.cursors
# Other
import webbrowser

# My modules
from hwrt.handwritten_data import HandwrittenData
from distance_metric import handwritten_data_greedy_matching_distance as dtw
from hwrt import preprocessing
from hwrt import utils


def update_data(cfg, a, unaccept=False):
    mysql = cfg['mysql_online']
    connection_local = pymysql.connect(host=mysql['host'],
                                       user=mysql['user'],
                                       passwd=mysql['passwd'],
                                       db=mysql['db'],
                                       cursorclass=pymysql.cursors.DictCursor)
    cursor_local = connection_local.cursor()
    if unaccept:
        sql = ("UPDATE `wm_raw_draw_data` "
               "SET  `administrator_edit` = now(), "
               "`missing_line` = %i, "
               "`has_hook` = %i, "
               "`has_too_long_line` = %i, "
               "`is_image` = %i, "
               "`other_problem` = %i, "
               "`has_interrupted_line` = %i, "
               "`accepted_formula_id` = NULL "
               "WHERE  `wm_raw_draw_data`.`id` =%i "
               "LIMIT 1;") % \
              (int(a.missing_line),
               int(a.has_hook),
               int(a.has_too_long_line),
               int(a.is_image),
               int(a.other_problem),
               int(a.has_interrupted_line),
               a.raw_data_id)
    elif a.istrash:
        sql = ("UPDATE `wm_raw_draw_data` "
               "SET  `administrator_edit` = now(), "
               "`missing_line` = %i, "
               "`has_hook` = %i, "
               "`has_too_long_line` = %i, "
               "`is_image` = %i, "
               "`other_problem` = %i, "
               "`has_interrupted_line` = %i, "
               "`accepted_formula_id` = 1 "
               "WHERE  `wm_raw_draw_data`.`id` =%i "
               "LIMIT 1;") % \
              (int(a.missing_line),
               int(a.has_hook),
               int(a.has_too_long_line),
               int(a.is_image),
               int(a.other_problem),
               int(a.has_interrupted_line),
               a.raw_data_id)
    else:
        sql = ("UPDATE `wm_raw_draw_data` "
               "SET  `administrator_edit` = now(), "
               "`missing_line` = %i, "
               "`has_hook` = %i, "
               "`has_too_long_line` = %i, "
               "`is_image` = %i, "
               "`other_problem` = %i, "
               "`has_interrupted_line` = %i "
               "WHERE  `wm_raw_draw_data`.`id` =%i "
               "LIMIT 1;") % \
              (int(a.missing_line),
               int(a.has_hook),
               int(a.has_too_long_line),
               int(a.is_image),
               int(a.other_problem),
               int(a.has_interrupted_line),
               a.raw_data_id)
    cursor_local.execute(sql)
    connection_local.commit()
    cursor_local.close()
    connection_local.close()
    connection_online = pymysql.connect(host=mysql['host'],
                                        user=mysql['user'],
                                        passwd=mysql['passwd'],
                                        db=mysql['db'],
                                        cursorclass=pymysql.cursors.DictCursor)
    cursor_online = connection_online.cursor()
    cursor_online.execute(sql)
    connection_online.commit()
    cursor_online.close()
    connection_online.close()


class HandwrittenDataM(HandwrittenData):
    def __init__(self,
                 raw_data_json,
                 formula_id,
                 wild_point_count,
                 missing_line,
                 has_hook,
                 has_too_long_line,
                 is_image,
                 other_problem,
                 has_interrupted_line,
                 raw_data_id,
                 latex):
        HandwrittenData.__init__(self, raw_data_json, formula_id)
        self.wild_point_count = wild_point_count
        self.missing_line = missing_line
        self.has_hook = has_hook
        self.has_too_long_line = has_too_long_line
        self.is_image = is_image
        self.other_problem = other_problem
        self.has_interrupted_line = has_interrupted_line
        self.unaccept = False
        self.ok = False
        self.raw_data_id = raw_data_id
        self.latex = latex
        self.istrash = False

    def show(self):
        import matplotlib.pyplot as plt
        from matplotlib.widgets import CheckButtons
        from matplotlib.widgets import Button
        fig, ax = plt.subplots()
        ax.set_title('Raw data id: %i, LaTeX: %s' % (self.raw_data_id,
                                                     self.latex))
        plt.subplots_adjust(bottom=0.3)

        for line in self.get_pointlist():
            xs, ys = [], []
            for p in line:
                xs.append(p['x'])
                ys.append(p['y'])
            ax.plot(xs, ys, '-o')
        ax.axis((0, 1, 0, 1))
        plt.gca().invert_yaxis()
        ax.set_aspect('equal')

        def handle_checkboxes(label):
            if label == 'other_problem':
                self.other_problem = not self.other_problem
            elif label == 'missing_line':
                self.missing_line = not self.missing_line
            elif label == 'has_hook':
                self.has_hook = not self.has_hook
            elif label == 'has_too_long_line':
                self.has_too_long_line = not self.has_too_long_line
            elif label == 'is_image':
                self.is_image = not self.is_image
            elif label == 'has_interrupted_line':
                self.has_interrupted_line = not self.has_interrupted_line
            plt.draw()

        checkpos = plt.axes([0.01, 0.05, 0.45, 0.2])
        check = CheckButtons(checkpos,
                             ('other_problem',
                              'has_interrupted_line',
                              'missing_line',
                              'has_hook',
                              'has_too_long_line',
                              'is_image'),
                             (self.other_problem,
                              self.has_interrupted_line,
                              self.missing_line,
                              self.has_hook,
                              self.has_too_long_line,
                              self.is_image))
        check.on_clicked(handle_checkboxes)

        def ok_function(a):
            self.ok = True
            plt.close()
        okpos = plt.axes([0.7, 0.05, 0.1, 0.075])
        ok_button = Button(okpos, 'OK')
        ok_button.on_clicked(ok_function)

        def unaccept_function(a):
            self.unaccept = True
            logger.info("unaccept raw_data_id %i" % self.raw_data_id)
            plt.close()
        unacceptpos = plt.axes([0.81, 0.05, 0.1, 0.075])
        unaccept_button = Button(unacceptpos, 'unaccept')
        unaccept_button.on_clicked(unaccept_function)

        def is_trash_function(a):
            a.istrash = True
            logger.info("trash raw_data_id %i" % self.raw_data_id)
            plt.close()
        is_trash_pos = plt.axes([0.7, 0.2, 0.1, 0.075])
        is_trash_button = Button(is_trash_pos, 'is_trash')
        is_trash_button.on_clicked(is_trash_function)

        # maximise height
        mng = plt.get_current_fig_manager()
        width, height = mng.window.maxsize()
        mng.resize(500, height)
        plt.axis('equal')
        plt.show()


def main(cfg, raw_data_start_id):
    mysql = cfg['mysql_online']
    connection = pymysql.connect(host=mysql['host'],
                                 user=mysql['user'],
                                 passwd=mysql['passwd'],
                                 db=mysql['db'],
                                 cursorclass=pymysql.cursors.DictCursor)
    cursor = connection.cursor()

    # Get formulas
    logger.info("Get formulas")
    print("get formulas")
    sql = ("SELECT `id`, `formula_in_latex` FROM `wm_formula` "
           "WHERE `id` > %s ORDER BY `id`")
    cursor.execute(sql, (raw_data_start_id, ))
    formulas = cursor.fetchall()
    formulaid2latex = {}
    for el in formulas:
        formulaid2latex[el['id']] = el['formula_in_latex']

    preprocessing_queue = [preprocessing.ScaleAndShift(),
                           # preprocessing.Douglas_peucker(EPSILON=0.2),
                           # preprocessing.Space_evenly(number=100,
                           #                            kind='cubic')
                           ]

    checked_formulas = 0
    checked_raw_data_instances = 0

    for formula_id in formulaid2latex.keys():
        alread_shown_in_browser = False
        if formula_id == 1:
            # This formula id is for trash. No need to look at it.
            continue
        # Get data
        logger.info("Get data for formula_id %i (%s)" %
                    (formula_id, formulaid2latex[formula_id]))
        sql = ("SELECT `id`, `data`, `accepted_formula_id`, "
               "`wild_point_count`, `missing_line`, `has_hook`, "
               "`has_too_long_line`, `is_image`, `administrator_edit`, "
               "`other_problem`, `has_interrupted_line` "
               "FROM  `wm_raw_draw_data` "
               "WHERE `accepted_formula_id` = %i "
               "ORDER BY `administrator_edit` DESC, "
               "`creation_date` ASC;") % formula_id
        cursor.execute(sql)
        raw_datasets = cursor.fetchall()
        logger.info("Raw datasets: %i" % len(raw_datasets))
        checked_raw_data_instances += len(raw_datasets)
        checked_formulas += 1
        if len(raw_datasets) < 100:
            continue
        As = []
        for i, data in enumerate(raw_datasets):
            if data['data'] == "[]":
                continue
            B = HandwrittenDataM(data['data'],
                                 data['accepted_formula_id'],
                                 data['wild_point_count'],
                                 data['missing_line'],
                                 data['has_hook'],
                                 data['has_too_long_line'],
                                 data['is_image'],
                                 data['other_problem'],
                                 data['has_interrupted_line'],
                                 data['id'],
                                 formulaid2latex[formula_id])
            B.preprocessing(preprocessing_queue)
            B_pll = B.get_pointlist()
            distance = float('inf')
            for A_pll in As:
                distance = min(distance, dtw(A_pll, B_pll))
            if distance > 100:
                if data['administrator_edit'] is not None:
                    As.append(B.get_pointlist())
                else:
                    if not alread_shown_in_browser:
                        alread_shown_in_browser = True
                        webbrowser.open("http://www.martin-thoma.de/"
                                        "write-math/view/?"
                                        "raw_data_id=%i" % data['id'], 2)
                    B.show()
                    if B.ok:
                        As.append(B.get_pointlist())
                        update_data(cfg, B)
                    else:
                        update_data(cfg, B, True)
        logger.info("[Status] Checked formulas: %i of %i" %
                    (checked_formulas, len(formulaid2latex)))
        logger.info("[Status] Checked raw_data_instances: %i" %
                    checked_raw_data_instances)
    logger.info("done")

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser(description=__doc__)

    # Add more options if you like
    parser.add_argument("-i", dest="i",
                        help="at which raw_data_id should it start?",
                        metavar="RAW_DATA_ID")
    args = parser.parse_args()
    cfg = utils.get_database_configuration()
    main(cfg, args.i)
