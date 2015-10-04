import urllib,time,random,re,traceback
import os,json
from bs4 import BeautifulSoup
start_time=time.time()
from collections import OrderedDict
exec(open('/home/fbbot/cfb/common_functions.py').read())
exec(open('/home/fbbot/cfb/sload.py').read())
msgs_already_sent=[]
scores_already_sent=[]
db={}
db['teams']=json.loads(sql.unique_get('data','teams'))
db['shorten']=json.loads(sql.unique_get('data','shorten'))
shorts=artolower(db['shorten'])
db['colors']=json.loads(sql.unique_get('data','colors'))
cis=artolower(db['colors'])
color_list=db['colors']
lastGames=json.loads(sql.unique_get('data','games_new')) #when you loop this, you can just run this at the beginning, then thereafter use the variable from the last run
db['games_new']=lastGames
rks=artolower(json.loads(sql.unique_get('data','ranks')))


def getGameInfo(typ): # retrieves game information from espn scoreboard (typ = 80 is fbs teams, typ = 81 is fcs teams)
	scoreboard=urllib.urlopen('http://espn.go.com/college-football/scoreboard/_/group/'+typ+'/year/2015/seasontype/2/?t='+str(time.time())).read()
	scoreboard=scoreboard[scoreboard.find('window.espn.scoreboardData 	= ')+len('window.espn.scoreboardData 	= '):]
	scoreboard=json.loads(scoreboard[:scoreboard.find('}};')+2])
	games={}
	for event in scoreboard['events']:
		this_game={}
		this_game['team2']=event['competitions'][0]['competitors'][0]['team']['location']
		this_game['team2score']=event['competitions'][0]['competitors'][0]['score']
		this_game['team1']=event['competitions'][0]['competitors'][1]['team']['location']
		this_game['team1score']=event['competitions'][0]['competitors'][1]['score']
		most_recent_play=''
		this_game['possession']=None
		if event['competitions'][0] != None and 'situation' in event['competitions'][0] and event['competitions'][0]['situation'] != None and  'lastPlay' in event['competitions'][0]['situation'] and event['competitions'][0]['situation']['lastPlay'] != None and 'text' in event['competitions'][0]['situation']['lastPlay']:
			most_recent_play=event['competitions'][0]['situation']['lastPlay']['text']
			if most_recent_play[0]=='(':
				most_recent_play=most_recent_play[1:]
				if most_recent_play[-1]==')': most_recent_play=most_recent_play[:-1]
			if 'downDistanceText' in event['competitions'][0]['situation']['lastPlay']:
				most_recent_play=most_recent_play+', '+event['competitions'][0]['situation']['lastPlay']['downDistanceText']
			if 'drive' in  event['competitions'][0]['situation']['lastPlay'] and 'description' in event['competitions'][0]['situation']['lastPlay']['drive']:
				most_recent_play=most_recent_play+' (This drive: '+event['competitions'][0]['situation']['lastPlay']['drive']['description']+')'
			if 'possession' in event['competitions'][0]['situation']: this_game['possession']=k4v(str(event['competitions'][0]['situation']['possession']),db['teams'])
		this_game['most_recent_play']=most_recent_play
		hometeam=''
		this_game['neutral']=True
		if event['competitions'][0]['competitors'][0]['homeAway']=='home':
			this_game['hometeam']=this_game['team2']
			this_game['neutral']=False
		elif event['competitions'][0]['competitors'][1]['homeAway']=='home':
			hometeam=this_game['team1']
			this_game['neutral']=False
		this_game['gid']=event['id']
		if 'weather' in event and 'temperature' in event['weather']: this_game['temperature']=event['weather']['temperature']
		else: this_game['temperature']=''
		this_game['status']=event['status']['type']['shortDetail']
		if 'broadcasts' in event['competitions'][0]['competitors']:
			this_game['network']=', '.join(event['competitions'][0]['competitors']['broadcasts'][0])
		else: this_game['network']=''
		games[this_game['team1']+this_game['team2']]=this_game
	return games # team1, team1score, team2, team2score, hometeam, neutral, temperature, status
keepGoing=True
try:
	while keepGoing:
		#Get our games
		games={}
		games['fcs']=getGameInfo('81')
		games['fbs']=getGameInfo('80')
		games['lastupdate']=int(time.time())
		if games['fcs'] != lastGames['fcs'] or games['fbs'] != lastGames['fbs']:
			sql.unique_set('data','games_new',json.dumps(games))
			#see if anything has changed for fbs teams. if so, send appropriate message
			for gid,gddt in games['fbs'].iteritems():
				st=gddt['status'].strip()
				score_code=gddt['team1']+gddt['team2']+gddt['team1score']+gddt['team2score']
				st=gddt['status'].strip()
				st=st.replace('15:00','BEGIN').replace(' IN ',' ')
				t1name=gddt['team1']
				t2name=gddt['team2']
				if t1name.lower() in shorts and shorts[t1name.lower()].strip() != '': t1name=shorts[t1name.lower()]
				if t2name.lower() in shorts and shorts[t2name.lower()].strip() != '': t2name=shorts[t2name.lower()]
				t1=t1name
				t2=t2name
				t1rk=''
				t2rk=''
				if gddt['team1'].lower() in rks and rks[gddt['team1'].lower()] != None: t1rk='('+rks[gddt['team1'].lower()]+') '
				if gddt['team2'].lower() in rks and rks[gddt['team2'].lower()] != None: t2rk='('+rks[gddt['team2'].lower()]+') '
				t1=t1rk+t1+' '+gddt['team1score']
				t2=t2rk+t2+' '+gddt['team2score']
				ntwkadd=''
				comm2=''
				poss=''
				mrcur=gddt['most_recent_play']
				comm2=mrcur.strip()
				if gddt['team2score'] > lastGames['fbs'][gid]['team2score'] or gddt['team1score'] > lastGames['fbs'][gid]['team1score']:
					if comm2 == '':
						if gddt['team2score'] > lastGames['fbs'][gid]['team2score']:
							if gddt['team2score'] == lastGames['fbs'][gid]['team2score']+3: comm2=gddt['team2']+' Field Goal GOOD.'
							elif gddt['team2score'] == lastGames['fbs'][gid]['team2score']+6: comm2=gddt['team2']+' Touchdown.'
							elif gddt['team2score'] == lastGames['fbs'][gid]['team2score']+7: comm2=gddt['team2']+' Touchdown and Extra Point GOOD.'
							elif gddt['team2score'] == lastGames['fbs'][gid]['team2score']+8: comm2=gddt['team2']+' Touchdown and Two Point Conversion.'
							elif gddt['team2score'] == lastGames['fbs'][gid]['team2score']+2: comm2=gddt['team2']+' Score.'
						if gddt['team1score'] > lastGames['fbs'][gid]['team1score']:
							if gddt['team1score'] == lastGames['fbs'][gid]['team1score']+3: comm2=gddt['team1']+' Field Goal GOOD.'
							elif gddt['team1score'] == lastGames['fbs'][gid]['team1score']+6: comm2=gddt['team1']+' Touchdown.'
							elif gddt['team1score'] == lastGames['fbs'][gid]['team1score']+7: comm2=gddt['team1']+' Touchdown and Extra Point GOOD.'
							elif gddt['team1score'] == lastGames['fbs'][gid]['team1score']+8: comm2=gddt['team1']+' Touchdown and Two Point Conversion.'
							elif gddt['team1score'] == lastGames['fbs'][gid]['team1score']+2: comm2=gddt['team1']+' Score.'
					#print comm2
					poss=gddt['possession']
				if poss != None:
					if poss.lower() == t1name.lower(): t1=t1+' (:)'
					elif poss.lower() == t2name.lower(): t2=t2+' (:)'
				if gddt['team1'].lower() in cis: t1=chr(3)+str(cis[gddt['team1'].lower()][0])+','+str(cis[gddt['team1'].lower()][1])+t1.strip()+chr(3)
				if gddt['team2'].lower() in cis: t2=chr(3)+str(cis[gddt['team2'].lower()][0])+','+str(cis[gddt['team2'].lower()][1])+t2.strip()+chr(3)
				if st.count('BEGIN') == 1 and st.count('1ST') == 1 and gid in db['ntwks']:
					ntwkadd=' - '+db['ntwks'][gid]
				if comm2 == '':
					datm=''
					datmn=''
					if gddt['team2score'] != lastGames['fbs'][gid]['team2score']:
						datm=gddt['team2']
						datmn='team2'
					elif gddt['team1score'] != lastGames['fbs'][gid]['team1score']:
						datm=gddt['team1']
						datmn='team1'
					if datm != '':
						dacomm=''
						if gddt[datmn+'score'] == int(lastGames['fbs'][gid][datmn+'score'])+6: dacomm=datm+' TOUCHDOWN!'
						if gddt[datmn+'score'] == int(lastGames['fbs'][gid][datmn+'score'])+3: dacomm=datm+' FIELD GOAL!'
						if gddt[datmn+'score'] == int(lastGames['fbs'][gid][datmn+'score'])+1: dacomm=datm+' EXTRA POINT GOOD!'
						if dacomm != '': comm2=dacomm
				stats_to_append=''
				if st.upper().count('FINAL') == 1 or st.upper().count('HALF') == 1:
					sts=stats(gddt['gid'])
					stats_to_append=' -- GAME STATS: '+sts+chr(3)
				if comm2.strip() != '': comm2=' '+comm2
				if gddt['neutral'] == True: cnctr='-'
				else: cnctr=' @ '
				msg='\x02'+t1+' '+cnctr+' '+t2+'\x02'+comm2+' ('+st+ntwkadd+')'+stats_to_append
				#new plays (for users requesting that info)
				#if gid in lastGames['fbs'] and gddt['most_recent_play'] != lastGames['fbs'][gid]['most_recent_play'] and gddt['most_recent_play'] != '':
				#	db['msgqueue']=json.loads(sql.unique_get('data','msgqueue'))
				#	db['msgqueue'].append([msg,'harkatmuld','NOTICE',None])
				#	sql.unique_set('data','msgqueue',json.dumps(db['msgqueue']))
				#new scores/big changes
				if gid in lastGames['fbs'] and gddt != lastGames['fbs'][gid]:
					if (((gddt['status'].upper().count('FINAL')==1  or gddt['status'].upper().count('OT') == 1 or gddt['status'].upper().count('15:00') != 0 or gddt['status'].upper().count('HALFTIME') != 0) and gddt['status'] != lastGames['fbs'][gid]['status']) or ((gddt['team1score'] > lastGames['fbs'][gid]['team1score']	or gddt['team2score'] > lastGames['fbs'][gid]['team2score']) and not score_code in scores_already_sent)):				
						if not msg in msgs_already_sent:
							db['msgqueue']=json.loads(sql.unique_get('data','msgqueue'))
							db['msgqueue'].append([msg,None,None,'score']) #when make it final, update to [msg,None,None,'score']
							sql.unique_set('data','msgqueue',json.dumps(db['msgqueue']))
							msgs_already_sent.append(msg)
							scores_already_sent.append(score_code)
		if json.dumps(games).count('team1score') == json.dumps(games).count('PM ET')+json.dumps(games).count('AM ET') or json.dumps(games).count('team1score') == json.dumps(games).count('DELAYED')+json.dumps(games).count('PM ET')+json.dumps(games).count('AM ET')+json.dumps(games).count('FINAL'):
			start_time=0
		if time.time() > start_time+60*4.8:
			keepGoing=False
		lastGames=games
		time.sleep(random.randrange(8,13))
except:
	errr=str(traceback.format_exc().replace('\n',''))
	errr=errr[errr.find(':')+2:]
	msgqueue=json.loads(sql.unique_get('data','msgqueue'))
	msgqueue.append([errr,'#cfbtest'])
	sql.unique_set('data','msgqueue',json.dumps(msgqueue))	