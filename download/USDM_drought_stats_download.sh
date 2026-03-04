AREA="HUCStatistics"
STATS_TYPE="GetDroughtSeverityStatisticsByAreaPercent"
AOI="14"
START_DATE="1/1/2000" # M/D/YYYY
END_DATE="12/31/2024" # M/D/YYYY
STATS_FORMAT="2" # 1 for traditional 2 for categorical
HUC=2 # size of HUC you want to use


wget "https://usdmdataservices.unl.edu/api/$AREA/$STATS_TYPE?aoi=$AOI&startdate=$START_DATE&enddate=$END_DATE&statisticsType=$STATS_FORMAT&hucLevel=$HUC" --output-document=USDM_HUC2_UpperColorado_2000-2024.csv

mv USDM_HUC2_UpperColorado_2000-2024.csv ../data/USDM_HUC2_UpperColorado_2000-2024.csv