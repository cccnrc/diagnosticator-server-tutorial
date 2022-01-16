#! /usr/bin/env python3.8

import redis
import json

def redis_connect( url, database, pwd = None ):
    '''
        connect to a specific redis DB giving URL in format: redis://localhost:6378
        and DB number ancd check connection
    '''
    ip = url.split('//')[1].split(':')[0]
    port = url.split(':')[-1]
    if not pwd:
        r = redis.Redis( host = ip, port = port, db = database )
    else:
        r = redis.Redis( host = ip, port = port, db = database, password = pwd )
    try:
        r.ping()
        return( r )
        # flash( 'Redis is running', 'success' )
    except redis.ConnectionError:
        print("Redis isn't running or unable to authenticate")
    return( None )





def redis_dict_insert( url, database, d_dict, key_prefix, pwd = None ):
    '''
        this insert VAR/SAMPLE/GENE dict in specified DB in URL
        and returns a dict organized as var_dict but with 0/1 value for every field based on insertion success
    '''
    r = redis_connect( url, database, pwd )
    d_dict_inserted = {}
    if r:
        with r.pipeline() as pipe:
            for d_name, d_sub_dict in d_dict.items():
                for subdict_name, subdict in d_sub_dict.items() :
                    for k_name, k_obj in subdict.items():
                        pipe.hset( '{0}:{1}'.format( key_prefix, d_name ), '{0}:{1}'.format(subdict_name, k_name), json.dumps(k_obj) )
                        ### initiate dict to store insertion results
                        if '{0}:{1}'.format( key_prefix, d_name ) in d_dict_inserted:
                            d_dict_inserted['{0}:{1}'.format( key_prefix, d_name )].update({ '{0}:{1}'.format(subdict_name, k_name) : { json.dumps(k_obj) : 0 } })
                        else:
                            d_dict_inserted.update({ '{0}:{1}'.format( key_prefix, d_name ) : { '{0}:{1}'.format(subdict_name, k_name) : { json.dumps(k_obj) : 0 } } })
            result_list = pipe.execute()
        ### update the insertion dict returned with 0/1 based on status
        i = 0
        for d_name, d_sub_dict in d_dict_inserted.items():
            for k, vv in d_sub_dict.items() :
                for v in vv:
                    d_dict_inserted[ d_name ][ k ][ v ] = result_list[i]
                    i += 1
        return( d_dict_inserted )
    return( None )


def redis_dict_return( url, database, key_prefix, key_value = None, pwd = None ):
    '''
        this returns the DICT assocaited with specific key prefix
    '''
    r = redis_connect( url, database, pwd )
    d = {}
    dd = {}
    search_string = "{}:*".format(key_prefix)
    if key_value:
        search_string = "{0}:{1}".format(key_prefix, key_value)
    if r:
        key_list = r.scan_iter(search_string)
        for k in key_list:
            d.update({ k : r.hgetall(k) })
        for k in d:
            key_name = k.decode('utf-8').replace('{}:'.format(key_prefix), '')
            sub_d = {}
            for kk,v in d[k].items():
                subdict_k, subdict_v = kk.decode('utf-8').split(':',1)
                if subdict_k in sub_d:
                    sub_d[subdict_k].update({ subdict_v : json.loads(v) })
                else:
                    sub_d.update({ subdict_k : { subdict_v : json.loads(v) } })
            dd.update({ key_name : sub_d })
        if key_value:
            dd = dd[ key_value ]
        dr = order_dict( dd )
        return( dr )
    return( None )


def order_dict(d):
    '''
        this is to order the returned dict
    '''
    r = {}
    dk = list(d.keys())
    dk.sort()
    for k in dk:
        if k in d:
            r.update({ k : d[k] })
    return(r)


def redis_add_dict_element( url, database, key_prefix, key_value, subdict_name, element_name, element_value, pwd = None ):
    r = redis_connect( url, database, pwd )
    d = redis_dict_return( url, database, key_prefix, key_value, pwd )
    ### if already at same value return
    if element_name in d:
        if d[ element_name ] == element_value:
            return(True)
        else:
            redis_update_dict_element( url, database, key_prefix, key_value, subdict_name, element_name, element_value, pwd )
    with r.pipeline() as pipe:
        pipe.hset( '{0}:{1}'.format( key_prefix, key_value ), '{0}:{1}'.format(subdict_name, element_name), json.dumps(element_value) )
        result = pipe.execute()
    if result[0] == 1:
        return( True )
    return( False )



def redis_update_dict_element( url, database, key_prefix, key_value, subdict_name, element_name, element_value, pwd = None ):
    r = redis_connect( url, database, pwd )
    d = redis_dict_return( url, database, key_prefix, key_value, pwd )
    ### if already at same value return
    if redis_deleteKEY( url, database, '{0}:{1}'.format( key_prefix, key_value ) ):
        if subdict_name in d:
            if element_name in d[subdict_name]:
                d[subdict_name][element_name] = element_value
            else:
                d[subdict_name].update({ element_name : element_value })
        else:
            d.update({ subdict_name : { element_name : element_value } })
        insert_dict = { key_value : d }
        if redis_dict_insert( url, database, insert_dict, key_prefix, pwd = None ):
            return( True )
    return( False )



def redis_keys_return( url, database, key_prefix, pwd = None ):
    '''
        this returns the KEYS assocaited with specific key prefix
    '''
    r = redis_connect( url, database, pwd )
    search_string = "{}:*".format(key_prefix)
    if r:
        key_list = r.scan_iter(search_string)
        if key_list:
            n_list = [ k.decode('utf-8').replace( "{}:".format(key_prefix), '' ) for k in key_list ]
            return( n_list )
    return( None )




def check_data_in_DB( url, database, pwd = None ):
    '''
        this returns T/F if any data in DB
    '''
    r = redis_connect( url, database, pwd )
    if r:
        if r.dbsize() > 0:
            return( True )
    return( False )




def redis_deleteDB( url, database, pwd = None ):
    '''
        this delete a DB
        and returns T/F
    '''
    r = redis_connect( url, database, pwd )
    if r:
        return(r.flushdb())
    return( False )


def redis_deleteKEY( url, database, key_value, pwd = None ):
    '''
        this delete a DB key
        and returns T/F
    '''
    r = redis_connect( url, database, pwd )
    if r:
        d = r.delete( key_value )
        if d == 1:
            return( True )
    return ( False )


def redis_bgsave( url, database, pwd = None ):
    '''
        save redis DB
    '''
    r = redis_connect( url, database, pwd )
    if r:
        return( r.bgsave() )
    return ( False )















###ENDc
