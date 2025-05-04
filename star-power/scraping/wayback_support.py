"""
Project Name: Star Power
File: wayback_support.py

Scrapes previous versions of rotten tomatoes and extracts them using wayback machine.

Author: Kyle Salgado-Gouker
"""

from datetime import datetime
import os
import json

import pandas as pd
import waybackpy
from bs4 import BeautifulSoup
import warnings

from access.paths import MOVIE_HTML_SAMPLE_DATA_DIRECTORY, DATA_DIRECTORY
from utils.utilities import show_df_info, pretty_print_df
from utils.web_utils import fetch_url_with_retry


def save_html_content(key, date, html_content):
    filename = f"{key}_{date.strftime('%Y-%m-%d')}.html"
    filepath = os.path.join(MOVIE_HTML_SAMPLE_DATA_DIRECTORY, filename)
    with open(filepath, "w", encoding='utf-8') as file:
        file.write(html_content)


def retrieve_wayback_tomato_scores_across_range(key, url, date1, date2):
    print(f"Building wayback list for {key} from {date1} to {date2}")
    dates = pd.date_range(date1, date2).tolist()
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
    wayback = waybackpy.Url(url, user_agent)
    scores = []

    for date in dates:
        try:
            archived = wayback.near(year=date.year, month=date.month, day=date.day).archive_url
            response = fetch_url_with_retry(archived)
            if response:
                page = response.text
                soup = BeautifulSoup(page, 'lxml')
                print(f"Found page for {date} and film {key}")
                tomato_data = get_tomato_data(soup)
                if all(value == "N/A" for value in tomato_data):
                    # Save HTML content if all returned values are "N/A"
                    save_html_content(key, date, page)
                scores.append(tomato_data + [date, key, url])
            else:
                scores.append(["N/A"] * 4 + [date, key, url])  # Handle case where response is None

        except Exception as e:
            print(f"Failed to fetch or parse data for {date}: {e}")
            scores.append(["N/A"] * 4 + [date, key, url])

    return scores


def build_wayback_content(row):
    date = row['release_date']
    data = retrieve_wayback_tomato_scores_across_range(row['Release'],
                                                       row['Rotten Tomatoes URL'],
                                                       date + pd.DateOffset(days=3),
                                                       date + pd.DateOffset(days=7))
    return data


def get_tomato_data_1(soup):
    print("trying tomato_data_1")
    try:
        json_data = json.loads(soup.find('script', id='scoreDetails').text)
        critic_score = json_data["scoreboard"]["tomatometerScore"]["score"]
        critic_ratings = json_data["scoreboard"]["tomatometerScore"]["ratingCount"]
        audience_score = json_data["scoreboard"]["audienceScore"]["score"]
        audience_ratings = json_data["scoreboard"]["audienceScore"]["ratingCount"]
        return [critic_score, critic_ratings, audience_score, audience_ratings]
    except Exception as e:
        return None


def get_tomato_data_2(soup):
    print("trying tomato_data_2")
    try:
        json_data = json.loads(soup.find('script', id='score-details-json').text)
        critic_score = json_data["modal"]["tomatometerScoreAll"]["score"]
        critic_ratings = json_data["modal"]["tomatometerScoreAll"]["ratingCount"]
        audience_score = json_data["modal"]["audienceScoreAll"]["score"]
        audience_ratings = json_data["modal"]["audienceScoreAll"]["ratingCount"]
        return [critic_score, critic_ratings, audience_score, audience_ratings]
    except Exception as e:
        return None


def get_tomato_data_3(soup):
    print("trying tomato_data_3")
    try:
        critic_score = soup.find("span", class_="mop-ratings-wrap__percentage").get_text().strip()
        critic_ratings = soup.find("small", class_="mop-ratings-wrap__text--small").get_text().strip()
        audience_score = soup.find_all("span", class_="mop-ratings-wrap__percentage")[1].get_text().strip()
        audience_ratings = soup.find("strong", class_="mop-ratings-wrap__text--small").get_text().strip().split(":")[
            1].strip()
        return [critic_score, critic_ratings, audience_score, audience_ratings]
    except Exception as e:
        return None


def get_tomato_data_4(soup):
    print("trying tomato_data_4")
    try:
        critic_score = soup.find("span", class_="meter-value superPageFontColor").get_text().strip()
        critic_ratings = soup.find("div", id="scoreStats").find_all("span")[5].get_text().strip()
        audience_score = soup.find("div", class_="meter-value").get_text().strip()
        audience_ratings = soup.find("div", class_="audience-info").find_all("div")[1].get_text().strip().split(":")[
            1].strip().replace(',', '')
        return [critic_score, critic_ratings, audience_score, audience_ratings]
    except Exception as e:
        return None


def get_tomato_data_5(soup):
    print("trying tomato_data_5")
    try:
        critic_score = soup.find("span", class_="meter-value superPageFontColor").get_text().strip()
        critic_ratings = soup.find("div", id="scoreStats").find_all("span")[5].get_text().strip()
        audience_score = soup.find_all("span", class_="meter-value superPageFontColor")[1].get_text().strip()
        audience_ratings = soup.find_all("div", class_="audience-info hidden-xs superPageFontColor")[1].find_all("div")[
            1].get_text().strip().split(":")[1].strip().replace(',', '')
        return [critic_score, critic_ratings, audience_score, audience_ratings]
    except Exception as e:
        return None


def get_tomato_data_6(soup):
    print("trying tomato_data_6")
    try:
        critic_score = soup.find("div", class_="col-sm-12").find_all("span", class_="meter-value superPageFontColor")[
            0].get_text().strip()
        critic_ratings = soup.find("div", class_="col-sm-12").find_all("span", itemprop="reviewCount ratingCount")[
            0].get_text().strip()
        audience_score = soup.find("div", class_="col-sm-12").find_all("span", class_="meter-value superPageFontColor")[
            1].get_text().strip()
        audience_ratings = \
        soup.find("div", class_="col-sm-8 col-xs-12 audiencepanel").find_all("meta", itemprop="ratingCount")[0][
            'content']
        return [critic_score, critic_ratings, audience_score, audience_ratings]
    except Exception as e:
        return None


def get_tomato_data_7(soup):
    print("trying tomato_data_7")
    try:
        # Extracting critic score and ratings
        critic_score = soup.find("span", itemprop="ratingValue").text
        critic_ratings = soup.find("span", itemprop="reviewCount ratingCount").text
        # Extracting audience score and ratings
        audience_score = soup.find("span", itemprop="ratingValue", class_="superPageFontColor").text
        audience_ratings = soup.find("meta", itemprop="ratingcount")["content"]
        return [critic_score, critic_ratings, audience_score, audience_ratings]
    except Exception as e:
        return None


def get_tomato_data_8(soup):
    print("trying tomato_data_8")
    try:
        critic_score = soup.find("span", class_="meter rotten numeric").text.strip()
        critic_ratings = soup.find("span", itemprop="reviewCount").text.strip()
        audience_score = soup.find("span", class_="meter spilled numeric").text.strip()
        audience_ratings = soup.find("p", class_="critic_stats").find_all("span")[2].text.strip().replace(',', '')
        return [critic_score, critic_ratings, audience_score, audience_ratings]
    except Exception as e:
        return None


def get_tomato_data_9(soup):
    print("trying tomato_data_9")
    try:
        all_critics_numbers = soup.find("div", id="all-critics-numbers")
        critic_score = all_critics_numbers.find("span", class_="meter rotten numeric").text.strip()
        critic_ratings = all_critics_numbers.find("p", class_="critic_stats").find("span",
                                                                                   itemprop="reviewCount").text.strip()

        fan_side = soup.find("a", class_="fan_side")
        audience_score = fan_side.find("span", class_="meter spilled numeric").text.strip()
        audience_ratings = fan_side.find("p", class_="critic_stats").find("span",
                                                                          class_="subText liked_it").find_next_sibling().text.strip().replace(
            ',', '')

        return [critic_score, critic_ratings, audience_score, audience_ratings]
    except Exception as e:
        return None


def get_tomato_data_10(soup):
    print("trying tomato_data_10")
    try:
        all_critics_numbers = soup.find("div", id="all-critics-numbers")
        critic_score = all_critics_numbers.find("span", class_="meter rotten numeric").text.strip()
        critic_ratings = all_critics_numbers.find("p", class_="critic_stats").find("span",
                                                                                   property="v:count").text.strip()

        fan_side = soup.find("div", class_="fan_side")
        audience_score = fan_side.find("span", class_="meter popcorn numeric").text.strip()
        audience_ratings = fan_side.find("p", class_="critic_stats").find("span",
                                                                          class_="subText liked_it").find_next_sibling().text.strip().replace(
            ',', '')

        return [critic_score, critic_ratings, audience_score, audience_ratings]
    except Exception as e:
        return None


def get_tomato_data_11(soup):
    print("trying tomato_data_11")
    try:
        tomato_numbers = soup.find("div", class_="tomato_numbers")
        critic_score = tomato_numbers.find("span", class_="meter certified numeric").text.strip()
        critic_ratings = tomato_numbers.find("p", class_="critic_stats").find("span", property="v:count").text.strip()

        fan_side = soup.find("div", class_="fan_side")
        audience_score = fan_side.find("span", class_="meter popcorn numeric").text.strip()
        audience_ratings = fan_side.find("p", class_="critic_stats").find("span",
                                                                          class_="subText liked_it").find_next_sibling().text.strip().replace(
            ',', '')

        return [critic_score, critic_ratings, audience_score, audience_ratings]
    except Exception as e:
        return None


# tomatometer data in table - esp 2005-2006
def get_tomato_data_12(soup):
    print("trying tomato_data_12")
    try:
        critic_score_element = soup.find("span", class_="movie-body-text-bold")
        critic_score = critic_score_element.text.strip()

        reviews_count_element = soup.find("span", class_="movie-body-text")
        critic_ratings = reviews_count_element.find("strong").text.split(":")[1].strip()
        audience_ratings = critic_ratings

        return [critic_score, critic_ratings, critic_score, audience_ratings]
    except Exception as e:
        return None


# 2006 data with json (has audience data!)
def get_tomato_data_13(soup):
    print("trying tomato_data_13")
    try:
        # Find the script element containing JSON data
        script_tag = soup.find('script', id="score-details-json")

        if script_tag:
            # Extract JSON data
            json_data = json.loads(script_tag.string)
            scoreboard = json_data['scoreboard']
            # Extract critic and audience scores and ratings
            critic_score = scoreboard['tomatometerScore']['value']
            critic_ratings = scoreboard['tomatometerScore']['ratingCount']
            audience_score = scoreboard['audienceScore']['value']
            audience_ratings = scoreboard['audienceScore']['ratingCount']

            return [critic_score, critic_ratings, audience_score, audience_ratings]
        else:
            return None

    except Exception as e:
        print(f"Error extracting data: {e}")
        return None


def get_tomato_data_14(soup):
    print("trying tomato_data_14")
    try:
        # Find the span element containing the critic score within the div with id 'tomatometer_score'
        tomatometer_score_div_element = soup.find('div', id='tomatometer_score')
        if tomatometer_score_div_element:
            critic_score_element = tomatometer_score_div_element.find('span')
            if critic_score_element:
                # Extract the text content of the span element for the critic score
                critic_score = critic_score_element.text.strip()
                # Find the span element containing the reviews count within the div with id 'tomatometer_data'
                tomatometer_data_div_element = soup.find('div', id='tomatometer_data')
                if tomatometer_data_div_element:
                    reviews_count_element = tomatometer_data_div_element.find('span')
                    if reviews_count_element:
                        # Extract the text content of the span element for the reviews count
                        critic_ratings = reviews_count_element.text.strip()

                        # Return the extracted data as a list
                        return [critic_score, critic_ratings, critic_score, critic_ratings]

        return None
    except Exception as e:
        print(f"Error extracting tomato data: {e}")
        return None


# 2007 Data
def get_tomato_data_15(soup):
    print("trying tomato_data_15")
    try:
        # Find the span element containing the critic score within the div with id 'tomatometer_score'
        critic_score_element = soup.find('div', id='critics_tomatometer_score_txt')
        if critic_score_element:
            critic_score = critic_score_element.text.strip()
            # Find the span element containing the reviews count within the div with id 'tomatometer_data'
            reviews_count_element = soup.find('div', id='critics_tomatometer_numbers_txt')
            if reviews_count_element:
                critic_ratings_element = reviews_count_element.find('span')
                # Extract the text content of the span element for the reviews count
                if critic_ratings_element:
                    critic_ratings = critic_ratings_element.text.strip()
                    # Return the extracted data as a list
                    return [critic_score, critic_ratings, critic_score, critic_ratings]
        return None
    except Exception as e:
        print(f"Error extracting tomato data: {e}")
        return None


def get_tomato_data_16(soup):
    print("trying tomato_data_16")
    try:
        # Find the scorePanel div
        score_panel_div = soup.find('div', id='scorePanel')
        if score_panel_div:
            # Find all spans containing rating values inside the scorePanel div
            rating_value_spans = score_panel_div.find_all('span', itemprop='ratingValue')
            # Extract the critic_score and audience_score from the rating_value_spans list
            critic_score = rating_value_spans[0].text.strip() if len(rating_value_spans) > 0 else None
            audience_score = rating_value_spans[2].text.strip() if len(rating_value_spans) > 2 else None

            # Find all spans containing review counts inside the scorePanel div
            review_count_spans = score_panel_div.find_all('span', itemprop='reviewCount ratingCount')
            # Extract the critic_ratings and audience_ratings from the review_count_spans list
            critic_ratings = review_count_spans[0].text.strip() if len(review_count_spans) > 0 else None
            audience_ratings = review_count_spans[2].text.strip() if len(review_count_spans) > 2 else None

            # Return the extracted data as a list
            return [critic_score, critic_ratings, audience_score, audience_ratings]
        else:
            return None
    except Exception as e:
        print(f"Error extracting tomato data: {e}")
        return None

    # 2008 data


def get_tomato_data_17(soup):
    print("trying tomato_data_17")
    try:
        # Find the tmeter_bar div
        tmeter_bar_div = soup.find('div', id='tmeter_bar')
        if tmeter_bar_div:
            # Find the span containing the critic reviews
            critic_reviews_span = tmeter_bar_div.find('span', class_='fl')
            # Extract the critic ratings
            critic_ratings = critic_reviews_span.text.strip() if critic_reviews_span else None

            # Find the div containing the text information
            tmeter_numbers_div = tmeter_bar_div.find('div', id='critics_tomatometer_numbers_txt')
            if tmeter_numbers_div:
                # Extract the text containing reviews counted, fresh, and rotten
                text_content = tmeter_numbers_div.text.strip()
                # Extract the number of reviews counted
                reviews_counted = text_content.split(':')[1].split()[0]

                # Return the extracted data as a list
                return [critic_ratings, reviews_counted, critic_ratings, reviews_counted]
            else:
                return None
        return None
    except Exception as e:
        print(f"Error extracting tomato data: {e}")
        return None


def get_tomato_data_18(soup):
    print("trying tomato_data_18")
    try:
        # find div class="meter_box left_door"
        tmeter_box_div = soup.find('div', class_='meter_box left_door')
        if tmeter_box_div:
            # Find critic score
            critic_score_span = tmeter_box_div.find('span', id='all-critics-meter', class_='meter rotten numeric ')
            if critic_score_span:
                critic_score = critic_score_span.get_text(strip=True)
                # Find audience score
                audience_score_span = tmeter_box_div.find('span', class_='meter popcorn numeric ')
                if audience_score_span:
                    audience_score = audience_score_span.get_text(strip=True)
                    # Find critic ratings
                    critic_ratings_span = tmeter_box_div.find('span', itemprop='reviewCount')
                    if critic_ratings_span:
                        critic_ratings = critic_ratings_span.get_text(strip=True)
                        # Find audience ratings
                        audience_ratings_span = tmeter_box_div.find('p', class_='critic_stats').find_all('span')[-1]
                        if audience_ratings_span:
                            audience_ratings = audience_ratings_span.get_text(strip=True)
                            return [critic_score, critic_ratings, audience_score, audience_ratings]
        # try another parser
        return None
    except Exception as e:
        print(f"Error extracting tomato data: {e}")
        return None


def get_tomato_data_19(soup):
    try:
        print("trying tomato_data_19")

        # Find the script tag containing the JSON data
        script_tags = soup.find_all("script", type="text/javascript")

        # Define a snippet that closely matches the target JSON data in the script tag
        target_snippet = 'root.RottenTomatoes.context.scoreInfo ='

        for script_tag in script_tags:
            if script_tag.string and target_snippet in script_tag.string:
                # Find the start of the JSON object
                start = script_tag.string.find(target_snippet) + len(target_snippet)
                # Substring to get just the JSON part
                json_string = script_tag.string[start:].split(';', 1)[0].strip()

                try:
                    # Parse the JSON data
                    data = json.loads(json_string)

                    # Extract critic score and number of reviews
                    critic_score = data['tomatometerAllCritics']['score']
                    critic_ratings = data['tomatometerAllCritics']['numberOfReviews']

                    return [critic_score, critic_ratings, critic_score, critic_ratings]
                except json.JSONDecodeError:
                    print("Error decoding JSON")
                    return None

        # Return None if no relevant data is found
        return None
    except Exception as e:
        # next parser
        return None


def get_tomato_data_20(soup):
    print("trying tomato_data_20")
    try:
        # Initialize the result list
        # Find the div containing critic and audience scores
        tmeter_box_div = soup.find('div', class_='meter_box right_door')
        if tmeter_box_div:
            # Extracting critic score and number of reviews
            critic_score_span = tmeter_box_div.find('span', id='all-critics-meter')
            critic_reviews_p = tmeter_box_div.find('span', itemprop='reviewCount')
            if critic_score_span and critic_reviews_p:
                critic_score = int(critic_score_span.text.strip())
                critic_ratings = int(critic_reviews_p.text.strip())
                # Extracting audience score and number of ratings
                audience_score_span = tmeter_box_div.find('span', class_='meter popcorn numeric')
                audience_ratings_p = tmeter_box_div.find('p', class_='critic_stats').find('span',
                                                                                          class_='subText liked_it')
                if audience_ratings_p:
                    br = audience_ratings_p.find_next_sibling('br')
                    if br:
                        user_ratings = br.next_sibling.strip()
                        if user_ratings and audience_score_span:
                            audience_score = int(audience_score_span.text.strip())
                            audience_ratings = int(audience_ratings_p.replace('User Ratings: ', '').replace(',', ''))
                            return [critic_score, critic_ratings, audience_score, audience_ratings]

        return None  # No meter_box div found
    except Exception as e:
        print(f"Error extracting tomato data: {e}")
        return None


def get_tomato_data_21(soup):
    print("trying tomato_data_21")
    try:
        # Find the tmeter_bar div
        tomatometer_div = soup.find('div', id='tomatometer')
        if tomatometer_div:
            # Find the span containing the critic reviews
            score_span = tomatometer_div.find('span', class_='percent')
            # Extract the critic ratings
            if score_span:
                critic_ratings = score_span.text.strip()
                # Find the div containing the additional data
                tomatometer_data_div = tomatometer_div.find('div', id='tomatometer_data')
                if tomatometer_data_div:
                    # Extract the number of reviews counted
                    reviews_counted_p = tomatometer_data_div.find('p', text=lambda t: 'Reviews Counted:' in t)
                    if reviews_counted_p:
                        reviews_counted = int(reviews_counted_p.text.split(': ')[1].strip())
                        # Return the extracted data as a list
                        return [critic_ratings, reviews_counted, critic_ratings, reviews_counted]
        return None
    except Exception as e:
        return None


# 2005 & 2006 data
def get_tomato_data_22(soup):
    print("trying tomato_data_22")
    try:
        # find div class="meter_box right_door"
        tmeter_box_div = soup.find('div', class_='meter_box right_door')
        if tmeter_box_div:
            # Find div for critics
            all_critics_numbers_div = tmeter_box_div.find('div', class_='critic_side_container',
                                                          itemprop="aggregateRating")
            critic_score = ""
            critic_ratings = ""
            if all_critics_numbers_div:
                critic_score_span = all_critics_numbers_div.find('span', itemprop="ratingValue")
                if critic_score_span:
                    critic_score = critic_score_span.text.strip()
                critic_stats_p = all_critics_numbers_div.find('p', class_='critic_stats')
                if critic_stats_p:
                    review_count_span = critic_stats_p.find('span', itemprop="reviewCount")
                    if review_count_span:
                        critic_ratings = review_count_span.text.strip()

            # Find div for audience
            fan_side_div = tmeter_box_div.find('div', class_='fan_side')
            audience_score = 0
            audience_ratings = 0
            if fan_side_div:
                audience_score_span = fan_side_div.find('span', class_="meter wts numeric")
                if audience_score_span:
                    audience_score = audience_score_span.text.strip()
                audience_stats_p = fan_side_div.find('p', class_="critic_stats")
                if audience_stats_p:
                    audience_ratings_text = audience_stats_p.text
                    if "User Ratings:" in audience_ratings_text:
                        audience_ratings = audience_ratings_text.split("User Ratings: ")[1].replace(',', '').strip()

            return [critic_score, critic_ratings, audience_score, audience_ratings]

        return None  # If no meter box div found
    except Exception as e:
        return None


def get_tomato_data(soup):
    parse_functions = [
        get_tomato_data_1, get_tomato_data_2, get_tomato_data_3,
        get_tomato_data_4, get_tomato_data_5, get_tomato_data_6,
        get_tomato_data_7, get_tomato_data_8, get_tomato_data_9,
        get_tomato_data_10, get_tomato_data_11, get_tomato_data_12,
        get_tomato_data_13, get_tomato_data_14, get_tomato_data_15,
        get_tomato_data_16, get_tomato_data_17, get_tomato_data_18,
        get_tomato_data_19, get_tomato_data_20, get_tomato_data_21,
        get_tomato_data_22
    ]

    for func in parse_functions:
        result = func(soup)
        if result:
            return result

    # If no function succeeds, return a default list indicating failure for each value
    return ["N/A"] * 4


def build_wayback_content(row):
    if pd.isna(row['Rotten Tomatoes URL']):
        # Immediately return a DataFrame with correct dtypes set but no data.
        return pd.DataFrame(
            columns=["critic_score", "critic_ratings", "audience_score", "audience_ratings", "Sample Date", "Film",
                     "Url Retrieved"])

    date = row['release_date']
    results = retrieve_wayback_tomato_scores_across_range(row['Release'], row['Rotten Tomatoes URL'],
                                                          date + pd.DateOffset(days=1),
                                                          date + pd.DateOffset(days=7))

    # Create a DataFrame from the results
    data_records = []
    for result in results:
        data_record = {
            "critic_score": result[0] if result[0] != "N/A" else pd.NA,
            "critic_ratings": result[1] if result[1] != "N/A" else pd.NA,
            "audience_score": result[2] if result[2] != "N/A" else pd.NA,
            "audience_ratings": result[3] if result[3] != "N/A" else pd.NA,
            "Sample Date": result[4],
            "Film": result[5],
            "Url Retrieved": result[6]
        }
        data_records.append(data_record)

    df = pd.DataFrame(data_records)
    return df[df.columns[df.notna().any()]]  # Exclude columns where all entries are NA


def sample_from_franchises(franchise_members_df):
    # Sample only one film from each year from 2005 onward
    current_year = datetime.now().year
    franchise_members_since_2005_df = franchise_members_df[
        (franchise_members_df['year'] >= 2005) & (franchise_members_df['year'] <= current_year)].copy()

    sample_films_df = franchise_members_since_2005_df.groupby('year').apply(lambda x: x.sample(1)).reset_index(drop=True)

    # Applying the function to each row and concatenating the results into a new DataFrame with defined dtypes
    dataframes = [build_wayback_content(row) for index, row in sample_films_df.iterrows()]

    sample_films_performance_df = pd.concat(dataframes, ignore_index=True)

    # Define the data types for your DataFrame columns
    sampled_film_dtypes = {
        "critic_score": "object",
        "critic_ratings": "object",
        "audience_score": "object",
        "audience_ratings": "object",
        "Sample Date": "datetime64[ns]",
        "Film": "object",
        "Url Retrieved": "object"
    }

    # Convert the DataFrame to use the specified dtypes
    sample_films_performance_df = sample_films_performance_df.astype(sampled_film_dtypes)

    show_df_info(sample_films_performance_df, "Sampled Franchise Members Performance")
    pretty_print_df(sample_films_performance_df, interesting_columns = ['Film', 'Sample Date', 'critic_ratings',
                                                                        'critic_score', 'audience_ratings',
                                                                        'audience_score'])

    sample_films_df = (sample_films_performance_df.groupby
            (sample_films_performance_df['release_date'].dt.year).apply(lambda x: x.sample(3)).reset_index(drop=True))
    scores = sample_films_df.apply(build_wayback_content)

    # Flatten the list of lists
    all_scores = [item for sublist in scores for item in sublist]
    scores_df = pd.DataFrame(all_scores, columns=['Critic Score', 'Audience Score', 'Critic Reviews',
                                                  'Audience Ratings', 'Date', 'Title'])


    scores_df.to_csv(DATA_DIRECTORY + "/filtered_wayback_scores.csv", index=False)
    return scores_df




