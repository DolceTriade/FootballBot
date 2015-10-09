lst=''
lstar=[]
ts=''
nextgames={}
status_replace={}
for b,a in db['games_new']['fbs'].iteritems():
	#print a
	if b != 'lastupdate':
		st=str(a['status']).lower()
		if st.count('pm et') != 0 or st.count('pm edt') != 0:
			stp=st.replace(' et','').replace(' edt','')
			yr=time.strftime('%Y')
			if st.count('jan') != 0:
				yr=str(int(yr)+1)
			stp=time.mktime(time.strptime(stp+' '+yr,'%m/%d - %I:%M %p %Y'))
			status_replace[b]=[a['status'],'- '+time.strftime('%a',time.localtime(stp))+', '+st.replace(' edt','').upper()]
			if len(nextgames) < 11: nextgames[b]=stp
			else:
				mva=max(nextgames,key=nextgames.get)
				if stp < nextgames[mva]:
					nextgames.pop(mva)
					nextgames[b]=stp
		if st.count('final') == 0 and st.count('delay') == 0 and st.count('am et') == 0 and st.count('pm et') == 0 and st.count('am edt') == 0 and st.count('pm edt') == 0 and st.count('cancel') == 0:
			lstar.append(gameInfo(b,False, False, True, True, '', True).strip())
			if lst=='':
				lst+=gameInfo(b,branked=True).strip()
			else:
				lst+=' '+chr(3)+'0,1, '+chr(3)+' '+gameInfo(b,branked=True).strip()
				ts+='PRIVMSG '+origin+' :'+lst+chr(3)+'\r\n'
#				db['msgqueue'].append([lst+chr(3),origin,'PRIVMSG'])
				lst=''
nextgames = sorted(nextgames.iteritems(), key=operator.itemgetter(1))
lst=lst.strip()
if lst == '' and ts == '':
	lst='There are no games on at the moment. '
ngl=''
print status_replace
for a in nextgames:
	nass=a[0]
	this_game_add=gameInfo(nass,score=False,branked=True).strip()
	if a[0] in status_replace: 
		print 'replacing'
		this_game_add=this_game_add.replace(status_replace[a[0]][0],status_replace[a[0]][1])
	ngl+=this_game_add+', '
ngl=ngl[:-2]
if len(nextgames) != 0 and lst == 'There are no games on at the moment. ': 
	lst+='\x02Upcoming games: \x02'+ngl+'\r\n'
	comb=lst
else:
	comb=', '.join(lstar)

if dest.lower()=='footballbot': msg_dest=origin
else: msg_dest=dest

user_pref=sql.get_user(origin)
msg_type='PRIVMSG'
if user_pref:
	if 'cmds' in user_pref and 'whatson' in user_pref['cmds']:
		if user_pref['cmds']['whatson']=='you': msg_dest=origin
		elif user_pref['cmds']['whatson']=='channel' and dest.lower()!='footballbot': msg_dest=dest
	if 'pers_msgs' in user_pref and msg_dest==origin:
		if user_pref['pers_msgs'] == 'notice': msg_type='NOTICE'
		elif user_pref['pers_msgs'] == 'message': msg_type='PRIVMSG'

for comb in splitMessage(comb,400,', '):
	db['msgqueue'].append([comb,msg_dest,msg_type])