<?php
include '../init.php';

$cachedir = '../cache-data/';
$datafile = 'ranking.json';
if (!is_file($cachedir.$datafile) || (time() - filemtime($cachedir.$datafile)) > 24*60*60) {
    // calculate data
    $sql = "SELECT `wm_users`.`id`, `display_name`, ".
           "COUNT(`wm_raw_draw_data`.`id`) as `written_formulas`, ".
           "COUNT(DISTINCT `accepted_formula_id`) as `distinct_symbols` ".
           "FROM `wm_raw_draw_data` ".
           "RIGHT JOIN `wm_users` ON `wm_users`.`id` = `user_id` ".
           "GROUP BY `user_id` ".
           "ORDER BY `written_formulas` DESC";
    $stmt = $pdo->prepare($sql);
    $stmt->execute();
    $users_by_raw_data = $stmt->fetchAll();

    $sql = "SELECT COUNT(`id`) as `written_formulas_total` ".
           "FROM `wm_raw_draw_data`";
    $stmt = $pdo->prepare($sql);
    $stmt->execute();
    $written_formulas_total = $stmt->fetchObject()->written_formulas_total;

    $sql = "SELECT COUNT(`id`) as `written_formulas_total`, ".
           "COUNT(DISTINCT `accepted_formula_id`) as `distinct_symbols_total`".
           "FROM `wm_raw_draw_data`";
    $stmt = $pdo->prepare($sql);
    $stmt->execute();
    $row = $stmt->fetchObject();
    $written_formulas_total = $row->written_formulas_total;
    $distinct_symbols_total = $row->distinct_symbols_total;

    // Write data to cache
    $data = array();
    $data['users_by_raw_data'] = $users_by_raw_data;
    $data['written_formulas_total'] = $written_formulas_total;
    $data['distinct_symbols_total'] = $distinct_symbols_total;

    $fp = fopen($cachedir.$datafile, 'w');
    fwrite($fp, json_encode($data));
    fclose($fp);
} else {
    $msg[] = array("class" => "alert-info",
                    "text" => "This is a cached version from ".
                               date("d.m.Y", filemtime($cachedir.$datafile)));
    $data = file_get_contents($cachedir.$datafile);
    $data = json_decode($data, true);
}


echo $twig->render('ranking.twig', array('heading' => 'Ranking',
                                       'file'=> "ranking",
                                       'logged_in' => is_logged_in(),
                                       'display_name' => $_SESSION['display_name'],
                                       'msg' => $msg,
                                       'users_by_raw_data' => $data['users_by_raw_data'],
                                       'written_formulas_total' => $data['written_formulas_total'],
                                       'distinct_symbols_total' => $data['distinct_symbols_total']
                                       )
                  );