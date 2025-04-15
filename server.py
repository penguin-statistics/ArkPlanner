import asyncio

import click
from sanic import Sanic, response
from MaterialPlanning import MaterialPlanning

app = Sanic('ArkPlanner')

app.static('/', './ArkPlannerWeb/index.html', name='web_index')
app.static('/css', './ArkPlannerWeb/css', name='css')
app.static('/fonts', './ArkPlannerWeb/fonts', name='fonts')
app.static('/img', './ArkPlannerWeb/img', name='img')
app.static('/js', './ArkPlannerWeb/js', name='js')

@app.before_server_start
async def init_mp(app):
    app.ctx.mp = MaterialPlanning()

@app.get('/', name='index')
async def index(request):
    return response.redirect("https://penguin-stats.io/planner")

@app.get('/_health', name='_health')
async def health(request):
    return response.json({"status": "ok"})

@app.post('/plan', name='plan')
async def plan(request):
    try:
        input_data = request.json
    except:
        return response.json({'error': True, 'reason': 'Uninterpretable input'})

    # get value by key or default
    # weak type checking only
    owned_dct = input_data.get('owned', {})
    required_dct = input_data.get('required', {})

    extra_outc = input_data.get('extra_outc', False)
    convertion_dr = input_data.get('convertion_dr', 0.18)
    exp_demand = input_data.get('exp_demand', True)
    gold_demand = input_data.get('gold_demand', True)
    exclude = input_data.get('exclude', [])

    store = input_data.get('store', False)
    input_lang = input_data.get('input_lang', 'zh')
    output_lang = input_data.get('output_lang', 'zh')
    server = input_data.get('server', 'CN')

    try:
        dct = app.ctx.mp.get_plan(
            required_dct, owned_dct, False,
            outcome=extra_outc,
            exp_demand=exp_demand,
            gold_demand=gold_demand,
            exclude=exclude,
            store=store,
            convertion_dr=convertion_dr,
            input_lang=input_lang,
            output_lang=output_lang,
            server=server
        )
    except ValueError as e:
        return response.json({'error': True, 'reason': f'{e}'})
    except Exception as e:
        return response.json({'error': True, 'reason': f'{e}'})
    return response.json(dct)


@app.after_server_start
async def update_each_half_hour(app, loop):
    while True:
        app.ctx.mp.update()
        await asyncio.sleep(30 * 60)


@click.command()
@click.option('-h', '--host', default='127.0.0.1', help='Binding address')
@click.option('-p', '--port', default=8000, help='Binding port')
@click.option('-w', '--workers', default=1, help='Number of worker')
@click.option('--debug', is_flag=True, default=False, help='Trigger Sanic debug mode')
@click.option('--log', is_flag=True, default=False, help='Trigger Sanic request log(will slows server)')
def start_server(host, port, workers, debug, log):
    app.run(host=host, port=port, workers=workers, debug=debug, access_log=log)

if __name__ == '__main__':
    start_server()
