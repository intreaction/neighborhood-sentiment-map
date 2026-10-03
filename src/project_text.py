"""Versioned provisional sentence rules, not a validated NLP classifier.

A clause needs explicit outdoor/place context for cleanliness and safety to count
as public-realm evidence. Uncertain targets remain uncertain. No demographic or
resident identity is inferred. VADER polarity is a lexical baseline.
"""
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
VERSION='place-clause-rules-v1'
ANALYZER=None
TOPIC_PATTERNS={
 'walking_accessibility':r'\b(?:walkable|walkability|walking distance|walking here|walk here|walk to|sidewalks?|crosswalks?|pedestrian|wheelchair|accessibility|accessible|bike lanes?|bike paths?|bicycle|cycling)\b',
 'transit':r'\b(?:transit|streetcar|light rail|subway|bus stop|bus station|train station|metro station)\b',
 'parking':r'\b(?:parking|parked|valet|garage)\b',
 'safety':r'\b(?:safe|unsafe|safety|dangerous|crime|robbed|mugged|sketchy|street lighting)\b',
 'cleanliness_maintenance':r'\b(?:clean|cleanliness|dirty|filthy|litter|trash|garbage|graffiti|potholes?|maintenance|neglected)\b',
 'public_space':r'\b(?:park|plaza|public square|greenway|public space|waterfront|riverfront|boardwalk|trail|fountain)\b',
 'construction':r'\b(?:construction|roadwork|road work|detour|scaffolding|torn up)\b',
 'food_service_value':r'\b(?:food|meal|service|staff|server|price|prices|expensive|affordable|delicious)\b',
 'neighborhood':r'\b(?:neighborhood|neighbourhood|surroundings|this area|part of town|revitalization)\b',
}
TOPICS={k:re.compile(v,re.I) for k,v in TOPIC_PATTERNS.items()}
ANY=re.compile('|'.join('(?:'+v+')' for v in TOPIC_PATTERNS.values()),re.I)
PLACE=re.compile(r'\b(?:street|sidewalk|neighborhood|neighbourhood|outside|surroundings|block|downtown|public|park|plaza|waterfront|riverfront|greenway|trail|boardwalk|crosswalk|walkable|walking distance|walking here|walk here|walk to|bike lane|bus stop|station|streetcar|transit|part of town|this area)\b',re.I)
BUSINESS=re.compile(r'\b(?:bathroom|restroom|kitchen|dining room|hotel room|inside|interior|table|server|staff|food|meal|own (?:parking )?(?:lot|garage)|their (?:parking )?(?:lot|garage)|restaurant.s (?:lot|garage))\b',re.I)
SPLIT=re.compile(r'(?<=[.!?;])\s+|\n+|\s+(?:but|however|although)\s+|,\s+(?:and|while)\s+',re.I)
ACCESS={'walking_accessibility','transit','parking'}
REALM={'safety','cleanliness_maintenance','public_space','construction','neighborhood'}
NEGATIVE=re.compile(r'\b(?:unsafe|dangerous|dirty|filthy|litter|garbage|potholes?|difficult|impossible|inaccessible|overcrowded|neglected|poor lighting|lack of|hard to|no sidewalks?|no parking|not safe|not clean|not accessible)\b',re.I)
NEGATED=re.compile(r'\b(?:not|never|no longer|isn.t|wasn.t)\s+(?:\w+\s+)?(?:unsafe|dangerous|dirty|difficult|inaccessible|hard)\b',re.I)


def analyze_text(text):
    global ANALYZER
    if ANALYZER is None:ANALYZER=SentimentIntensityAnalyzer()
    compound=ANALYZER.polarity_scores(text)['compound']
    evidence=[]; flags={}; place=False;access=False;realm=False
    if ANY.search(text):
        for clause in SPLIT.split(text):
            clause=clause.strip()
            if not clause:continue
            hits=[k for k,rx in TOPICS.items() if rx.search(clause)]
            if not hits:continue
            outdoor=bool(PLACE.search(clause));business=bool(BUSINESS.search(clause))
            score=ANALYZER.polarity_scores(clause)['compound']
            # Explicit negated barriers should not be counted as complaints.
            neg=bool(NEGATIVE.search(clause)) and not NEGATED.search(clause)
            polarity='negative' if neg or score <= -.05 else 'positive' if score >= .05 else 'neutral'
            for topic in hits:
                target='business' if topic=='food_service_value' else ('area' if outdoor and not business else 'business' if business and not outdoor else 'unclear')
                # Transit and clearly public infrastructure imply an outdoor target.
                if topic in ('transit','walking_accessibility') and not business:target='area'
                is_place=target=='area'
                place |= is_place
                negative=is_place and polarity=='negative'
                access |= negative and topic in ACCESS
                realm |= negative and topic in REALM
                old=flags.setdefault(topic,{'negative':False,'area':False})
                old['negative'] |= negative;old['area'] |= is_place
                evidence.append({'topic':topic,'target':target,'polarity':polarity,'text':clause[:240],'compound':score})
    return {'compound':compound,'place':place,'access_friction':access,'public_realm_complaint':realm,'topics':flags,'evidence':evidence}
