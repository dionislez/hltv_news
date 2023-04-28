async def html_overview_check(index: int, format_stat: str, overview_: dict):
    match index:
        case 0:
            format_stat = format_stat.replace('Total kills', '')
            overview_['total_kills'] = int(format_stat)
        case 1:
            format_stat = format_stat.replace('Headshot %', '').replace('%', '')
            overview_['perc_headshot'] = float(format_stat)
        case 2:
            format_stat = format_stat.replace('Total deaths', '')
            overview_['total_deaths'] = int(format_stat)
        case 3:
            format_stat = format_stat.replace('K/D Ratio', '')
            overview_['k_d'] = float(format_stat)
        case 4:
            format_stat = format_stat.replace('Damage / Round', '')
            overview_['dmg_rnd'] = float(format_stat)
        case 5:
            format_stat = format_stat.replace('Grenade dmg / Round', '')
            overview_['gnd_dmg_rnd'] = float(format_stat)
        case 6:
            format_stat = format_stat.replace('Maps played', '')
            overview_['maps_played'] = int(format_stat)
        case 7:
            format_stat = format_stat.replace('Rounds played', '')
            overview_['rnds_played'] = int(format_stat)
        case 8:
            format_stat = format_stat.replace('Kills / round', '')
            overview_['kills_rnd'] = float(format_stat)
        case 9:
            format_stat = format_stat.replace('Assists / round', '')
            overview_['assists_rnd'] = float(format_stat)
        case 10:
            format_stat = format_stat.replace('Deaths / round', '')
            overview_['dths_rnd'] = float(format_stat)
        case 11:
            format_stat = format_stat.replace('Saved by teammate / round', '')
            overview_['sav_by_tmt_rnd'] = float(format_stat)
        case 12:
            format_stat = format_stat.replace('Saved teammates / round', '')
            overview_['sav_tmts_rnd'] = float(format_stat)
        case 13:
            format_stat = format_stat.replace('Rating 1.0', '').replace('Rating 2.0', '')
            overview_['rating'] = float(format_stat)

async def html_individual_check(index: int, format_stat: str, overview_: dict):
    match index:
        case 4:
            format_stat = format_stat.replace('Rounds with kills', '')
            overview_['rnds_with_kills'] = int(format_stat)
        case 5:
            format_stat = format_stat.replace('Kill - Death differenceK - D diff.', '')
            overview_['k_d_diff'] = int(format_stat)
        case 6:
            format_stat = format_stat.replace('Total opening kills', '')
            overview_['open_k'] = int(format_stat)
        case 7:
            format_stat = format_stat.replace('Total opening deaths', '')
            overview_['open_d'] = int(format_stat)
        case 8:
            format_stat = format_stat.replace('Opening kill ratio', '')
            overview_['kill_ratio'] = float(format_stat)
        case 10:
            format_stat = format_stat.replace('Team win percent after first kill', '').replace('%', '')
            overview_['perc_team_win_first_k'] = float(format_stat)
        case 11:
            format_stat = format_stat.replace('First kill in won rounds', '').replace('%', '')
            overview_['perc_first_k_win_rnds'] = float(format_stat)
        case 12:
            format_stat = format_stat.replace('0 kill rounds', '')
            overview_['0_k_rnds'] = int(format_stat)
        case 13:
            format_stat = format_stat.replace('1 kill rounds', '')
            overview_['1_k_rnds'] = int(format_stat)
        case 14:
            format_stat = format_stat.replace('2 kill rounds', '')
            overview_['2_k_rnds'] = int(format_stat)
        case 15:
            format_stat = format_stat.replace('3 kill rounds', '')
            overview_['3_k_rnds'] = int(format_stat)
        case 16:
            format_stat = format_stat.replace('4 kill rounds', '')
            overview_['4_k_rnds'] = int(format_stat)
        case 17:
            format_stat = format_stat.replace('5 kill rounds', '')
            overview_['5_k_rnds'] = int(format_stat)
        case 18:
            format_stat = format_stat.replace('Rifle kills', '')
            overview_['riffle_k'] = int(format_stat)
        case 19:
            format_stat = format_stat.replace('Sniper kills', '')
            overview_['sniper_k'] = int(format_stat)
        case 20:
            format_stat = format_stat.replace('SMG kills', '')
            overview_['smg_k'] = int(format_stat)
        case 21:
            format_stat = format_stat.replace('Pistol kills', '')
            overview_['pistol_k'] = int(format_stat)
        case 22:
            format_stat = format_stat.replace('Grenade', '')
            overview_['grenade_k'] = int(format_stat)
        case 23:
            format_stat = format_stat.replace('Other', '')
            overview_['other_k'] = int(format_stat)

async def hltv_career_check(index: int, format_stat: str, overview_: dict):
    match index:
        case 0:
            overview_['all'] = 0 if format_stat == '-' else float(format_stat)
        case 1:
            overview_['online'] = 0 if format_stat == '-' else float(format_stat)
        case 2:
            overview_['lan'] = 0 if format_stat == '-' else float(format_stat)
        case 3:
            overview_['major'] = 0 if format_stat == '-' else float(format_stat)