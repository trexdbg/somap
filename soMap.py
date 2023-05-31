import streamlit as st
import pandas as pd
from gql import Client, gql                                                                                                                                                                                                                
from gqlactioncable import ActionCableWebsocketsTransport
import requests
import plotly.express as px
import numpy as np
from PIL import Image
from io import BytesIO

st.set_page_config(layout="wide")

apiSo = st.secrets["apiSo"]

url = 'https://api.sorare.com/graphql'

def listClubs(league):

    query_clubs_compet = f"""{{competition(slug:"{league}")
                {{
                    clubs
                    {{
                        nodes
                            {{
                                slug
                                name
                            }}
                        }}
                    }}
                }}"""

    r = requests.post(url, json={'query': query_clubs_compet}, headers={'APIKEY':apiSo})

    return r.json()['data']['competition']['clubs']['nodes']

st.cache_data(ttl=1000)
def listPlayers(clubNameGk):
    
    query_clubs_compet = f"""{{club(slug:"{clubNameGk}")
                {{
                    activePlayers
                    {{
                        nodes
                            {{
                                displayName
                                pictureUrl
                                positionTyped
                                appearances
                                averageScore(type:LAST_FIVE_SO5_AVERAGE_SCORE)
                            }}
                        }}
                    }}
                }}"""

    r = requests.post(url, json={'query': query_clubs_compet}, headers={'APIKEY':apiSo})
    return r.json()


choiceLeagues = st.selectbox('Choisir un championat',[
    "ligue-1-fr",
    "premier-league-gb-eng",
    "serie-a-it",
    "laliga-santander",
    "bundesliga-de",
    "eredivisie",
    "jupiler-pro-league"
])



lc = listClubs(choiceLeagues)

listTeam = []
for items in lc:

    t = listPlayers(items['slug'])
    df = pd.DataFrame(t['data']['club']['activePlayers']['nodes'])
    df['clubName'] = items['name']
    df['competition'] = choiceLeagues
    listTeam.append(df)

dfAll = pd.concat(listTeam)
dfAll = dfAll[dfAll['averageScore'] > 0]

choicePosition = st.sidebar.multiselect('position',dfAll.positionTyped.unique())

dfResult = dfAll[dfAll['positionTyped'].isin(choicePosition)]
if len(choicePosition) == 0 :
    dfResult = dfAll


fig = px.treemap(dfResult, path=['clubName','displayName'], 
                 values='averageScore',
                 color='averageScore',
                 color_continuous_scale='RdBu',
                 color_continuous_midpoint=np.average(df['averageScore'], weights=df['averageScore']))

index_level_1 = [i for i, parent in enumerate(fig.data[0].parents) if parent == '']

fig.update_traces(marker=dict(cornerradius=5))
fig.data[0].marker.line.width = [3 if i in index_level_1 else 1 for i in range(len(fig.data[0].labels))]


fig.data[0].customdata = dfResult[['averageScore','positionTyped']]
fig.data[0].texttemplate = "%{label}<br>%{customdata[0]}<br>%{customdata[1]}"

st.plotly_chart(fig, use_container_width=True)

sortdf = dfResult.sort_values(by='averageScore', ascending=False)


cols = st.columns(5)
for e, p in enumerate(sortdf.head(5)[['displayName','pictureUrl','averageScore']].to_dict(orient='records')):
    cols[e].write(p['displayName'])
    if p['pictureUrl'] is not None:
        response = requests.get(p['pictureUrl'])
        image = Image.open(BytesIO(response.content))
        image_resized = image.resize((300, 400))
        image_cropped = image_resized.crop((0, 0, 300, 300))
        cols[e].image(image_cropped)
    cols[e].title(p['averageScore'])