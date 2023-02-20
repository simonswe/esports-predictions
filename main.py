from pprint import pprint
from bs4 import BeautifulSoup

import tzlocal
import requests
import datetime
import converters
import time
import zoneinfo

HLTV_COOKIE_TIMEZONE = "America/New_York"
HLTV_ZONEINFO = zoneinfo.ZoneInfo(HLTV_COOKIE_TIMEZONE)

LOCAL_TIMEZONE_NAME = tzlocal.get_localzone_name()
LOCAL_ZONEINFO = zoneinfo.ZoneInfo(LOCAL_TIMEZONE_NAME)

TEAM_MAP_FOR_RESULTS = []


def get_all_teams():
    if not TEAM_MAP_FOR_RESULTS:
        teams = getParsedPage("https://www.hltv.org/stats/teams?minMapCount=0")
        for team in teams.find_all("td", {"class": ["teamCol-teams-overview"], }):
            team = {'id': converters.to_int(team.find("a")["href"].split("/")[-2]), 'name': team.find("a").text,
                    'url': "https://hltv.org" + team.find("a")["href"]}
            TEAM_MAP_FOR_RESULTS.append(team)


def findTeamId(teamName: str):
    get_all_teams()
    for team in TEAM_MAP_FOR_RESULTS:
        if team['name'] == teamName:
            return team['id']
    return None


def padIfNeeded(numberStr: str):
    if int(numberStr) < 10:
        return str(numberStr).zfill(2)
    else:
        return str(numberStr)


def monthNameToNumber(monthName: str):
    # Check for the input "Augu" and convert it to "August"
    # This is necessary because the input string may have been sanitized
    # by removing the "st" from the day numbers, such as "21st" -> "21"
    if monthName == "Augu":
        monthName = "August"
    return datetime.datetime.strptime(monthName, '%B').month


def getParsedPage(url, delay=0.5):
    headers = {
        "referer": "https://www.hltv.org/stats",
    }

    cookies = {
        "hltvTimeZone": HLTV_COOKIE_TIMEZONE
    }

    time.sleep(delay)

    return BeautifulSoup(requests.get(url, headers=headers, cookies=cookies).text, "lxml")


def getResultsIem():
    results = getParsedPage("https://www.hltv.org/results?event=6809")

    results_list = []

    pastResults = results.find_all("div", {"class": "results-holder"})

    for result in pastResults:
        resultDiv = result.find_all("div", {"class": "result-con"})

        for res in resultDiv:
            resultObj = {'url': "https://hltv.org" + res.find("a", {"class": "a-reset"}).get("href"),
                         'match-id': converters.to_int(res.find("a", {"class": "a-reset"}).get("href").split("/")[-2])}

            if res.parent.find("span", {"class": "standard-headline"}):
                dateText = res.parent.find("span", {"class": "standard-headline"}).text.replace("Results for ",
                                                                                                "").replace("th",
                                                                                                            "").replace(
                    "rd", "").replace("st", "").replace("nd", "")

                dateArr = dateText.split()

                dateTextFromArrPadded = padIfNeeded(dateArr[2]) + "-" + padIfNeeded(
                    monthNameToNumber(dateArr[0])) + "-" + padIfNeeded(dateArr[1])
                dateFromHLTV = datetime.datetime.strptime(dateTextFromArrPadded, '%Y-%m-%d').replace(
                    tzinfo=HLTV_ZONEINFO)
                dateFromHLTV = dateFromHLTV.astimezone(LOCAL_ZONEINFO)

                resultObj['date'] = dateFromHLTV.strftime('%Y-%m-%d')
            else:
                dt = datetime.date.today()
                resultObj['date'] = str(dt.day) + '/' + str(dt.month) + '/' + str(dt.year)

            if res.find("td", {"class": "placeholder-text-cell"}):
                resultObj['event'] = res.find("td", {"class": "placeholder-text-cell"}).text
            elif res.find("td", {"class": "event"}):
                resultObj['event'] = res.find("td", {"class": "event"}).text
            else:
                resultObj['event'] = None

            if res.find_all("td", {"class": "team-cell"}):
                resultObj['team1'] = res.find_all("td", {"class": "team-cell"})[0].text.lstrip().rstrip()
                resultObj['team1score'] = converters.to_int(
                    res.find("td", {"class": "result-score"}).find_all("span")[0].text.lstrip().rstrip())
                resultObj['team1-id'] = findTeamId(
                    res.find_all("td", {"class": "team-cell"})[0].text.lstrip().rstrip())
                resultObj['team2'] = res.find_all("td", {"class": "team-cell"})[1].text.lstrip().rstrip()
                resultObj['team2-id'] = findTeamId(
                    res.find_all("td", {"class": "team-cell"})[1].text.lstrip().rstrip())
                resultObj['team2score'] = converters.to_int(
                    res.find("td", {"class": "result-score"}).find_all("span")[1].text.lstrip().rstrip())
            else:
                resultObj['team1'] = None
                resultObj['team1-id'] = None
                resultObj['team1score'] = None
                resultObj['team2'] = None
                resultObj['team2-id'] = None
                resultObj['team2score'] = None

            results_list.append(resultObj)

    return results_list


def getResultsMatchURL(url):
    results = getParsedPage(url)

    resultObj = {}

    # OVERALL
    resultObj['date'] = results.find_all("div", {"class": "date"})[0].text.lstrip().rstrip()
    resultObj['team1'] = results.find_all("div", {"class": "teamName"})[0].text.lstrip().rstrip()
    resultObj['team1-score'] = results.find_all("div", {"class": "won"})[0].text.lstrip().rstrip()
    resultObj['team2'] = results.find_all("div", {"class": "teamName"})[1].text.lstrip().rstrip()
    resultObj['team2-score'] = results.find_all("div", {"class": "lost"})[0].text.lstrip().rstrip()

    mapCount = 0
    for x in results.find_all("div", {"class": "mapholder"}):
        mapCount += 1
        if x.find("div", {"class": "optional"}):
            resultObj['map' + str(mapCount)] = None
            resultObj['map' + str(mapCount) + '-team1-score'] = None
            resultObj['map' + str(mapCount) + '-team2-score'] = None
            resultObj['map' + str(mapCount) + '-team1-' + side1Team + '-side'] = None
            resultObj['map' + str(mapCount) + '-team2-' + side1Team + '-side'] = None
            resultObj['map' + str(mapCount) + '-team1-' + side1Team + '-side'] = None
            resultObj['map' + str(mapCount) + '-team2-' + side1Team + '-side'] = None
        else:
            resultObj['map' + str(mapCount)] = x.find("div", {"class": "mapname"}).text.lstrip().rstrip()
            resultObj['map' + str(mapCount) + '-team1-score'] = \
                x.find_all("div", {"class": "results-team-score"})[0].text.lstrip().rstrip()
            resultObj['map' + str(mapCount) + '-team2-score'] = \
                x.find_all("div", {"class": "results-team-score"})[1].text.lstrip().rstrip()
            # find ct and t scores
            sideScore = x.find("div", {"class": "results-center-half-score"})
            mapSpanCount = len(sideScore.find_all("span"))
            side1Team = sideScore.find_all("span")[1]['class'][0]
            resultObj['map' + str(mapCount) + '-team1-' + side1Team + '-side'] = \
                sideScore.find_all("span")[1].text.lstrip().rstrip()
            side1Team = sideScore.find_all("span")[3]['class'][0]
            resultObj['map' + str(mapCount) + '-team2-' + side1Team + '-side'] = \
                sideScore.find_all("span")[3].text.lstrip().rstrip()
            side1Team = sideScore.find_all("span")[5]['class'][0]
            resultObj['map' + str(mapCount) + '-team1-' + side1Team + '-side'] = \
                sideScore.find_all("span")[5].text.lstrip().rstrip()
            side1Team = sideScore.find_all("span")[7]['class'][0]
            resultObj['map' + str(mapCount) + '-team2-' + side1Team + '-side'] = \
                sideScore.find_all("span")[7].text.lstrip().rstrip()

            # check ot

            if mapSpanCount > 10:
                resultObj['map' + str(mapCount) + '-team1-ot'] = sideScore.find_all("span")[11].text.lstrip().rstrip()
                resultObj['map' + str(mapCount) + '-team2-ot'] = sideScore.find_all("span")[13].text.lstrip().rstrip()
            else:
                resultObj['map' + str(mapCount) + '-team1-ot'] = None
                resultObj['map' + str(mapCount) + '-team2-ot'] = None

    return resultObj


def getResultsIem1():
    results = getParsedPage("https://www.hltv.org/results?event=6809")

    results_list = []

    pastresults = results.find_all("div", {"class": "results-holder"})

    for result in pastresults:
        resultDiv = result.find_all("div", {"class": "result-con"})

        for res in resultDiv:
            url = "https://hltv.org" + res.find("a", {"class": "a-reset"}).get("href")
            results_list.append(getResultsMatchURL(url))

    return results_list

pprint(getResultsIem1())
# pprint(getResultsMatchURL("https://www.hltv.org/matches/2361341/liquid-vs-vitality-iem-katowice-2023"))
# pprint(getResultsMatchURL("https://www.hltv.org/matches/2361343/g2-vs-liquid-iem-katowice-2023"))