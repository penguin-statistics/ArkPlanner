from sanic import Sanic, response
from MaterialPlanning import MaterialPlanning
import time, codecs

app = Sanic()

app.static('/', './ArkPlannerWeb/index.html')
app.static('/css', './ArkPlannerWeb/css')
app.static('/fonts', './ArkPlannerWeb/fonts')
app.static('/img', './ArkPlannerWeb/img')
app.static('/js', './ArkPlannerWeb/js')


mp = MaterialPlanning()
mp.update()
last_updated = time.time()

@app.route("/plan", methods=['POST'])
async def plan(request):
    global last_updated
    try:
        input_data = request.json
        owned_dct = input_data["owned"]
        required_dct = input_data["required"]
    except:
        return response.json({"error": True, "reason": "Uninterpretable input"})

    try:
        extra_outc = request.json["extra_outc"]
    except:
        extra_outc = False

    try:
        exp_demand = request.json["exp_demand"]
    except:
        exp_demand = True

    try:
        gold_demand = request.json["gold_demand"]
    except:
        gold_demand = True

    try:
        if time.time() - last_updated > 60 * 30:
            mp.update()
            last_updated = time.time()
        dct = mp.get_plan(required_dct, owned_dct, False, 
                          outcome=extra_outc, exp_demand=exp_demand, gold_demand=gold_demand)
    except ValueError as e:
        return response.json({"error": True, "reason": str(e)})

    return response.json(dct)

# def get_costume_counts(countdir='costume_counts.txt'):
#     global costume_counts
#     try:
#         with codecs.open(countdir, 'r', 'utf-8') as f:
#             costume_counts = f.readline()



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
