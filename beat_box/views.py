import copy
import json

from rest_framework.request import override_method

from django.http import HttpResponse
from django.shortcuts import render

from . import api

def login(request):
    return render(request, 'beat_box/base.html')

def base_view(request):
    view = api.SuggestionViewSet.as_view({'get': 'list'})
    response = view(request)
    context = {
        'data': response.data,
    }
    return render(request, 'beat_box/suggestions.html', context)

def info(request):
    from rest_framework.metadata import SimpleMetadata
    metadata = SimpleMetadata().get_serializer_info(api.Suggestion())
    data = {
        'request': extract(copy.deepcopy(metadata), kind='request'),
        'response': extract(copy.deepcopy(metadata), kind='response'),
    }
    return HttpResponse(json.dumps(data, indent=4), content_type='application/json')

def extract(d, kind='response'):
    ret = {}
    for k, v in d.items():
        read_only = v.pop('read_only', False)
        write_only = v.pop('write_only', False)
        if kind == 'response':
            if write_only:
                continue
            v.pop('default')
            v.pop('required')
        elif kind == 'request':
            if read_only:
                continue
        if v.get('children'):
            v['children'] = extract(v['children'], kind)
        ret[k] = v
    return ret
