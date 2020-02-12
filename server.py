import time
import asyncio
from sanic import Sanic, response
from MaterialPlanning import MaterialPlanning

app = Sanic()

app.static('/', './ArkPlannerWeb/index.html')
app.static('/css', './ArkPlannerWeb/css')
app.static('/fonts', './ArkPlannerWeb/fonts')
app.static('/img', './ArkPlannerWeb/img')
app.static('/js', './ArkPlannerWeb/js')

mp = MaterialPlanning()
mp.update()

@app.route("/plan", methods=['POST'])
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
    exp_demand = input_data.get('exp_demand', True)
    gold_demand = input_data.get('gold_demand', True)
    exclude = input_data.get('exclude', [])

    try:
        dct = mp.get_plan(
            required_dct, owned_dct, False,
            outcome=extra_outc,
            exp_demand=exp_demand,
            gold_demand=gold_demand,
            exclude=exclude,
        )
    except ValueError as e:
        return response.json({'error': True, 'reason': f'{e}'})
    except Exception as e:
        return response.json({'error': True, 'reason': 'Unexpected Error'})
    return response.json(dct)


@app.listener('after_server_start')
async def update_each_half_hour(app, loop):
    while True:
        mp.update()
        await asyncio.sleep(30 * 60)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
