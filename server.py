from sanic import Sanic, response
from MaterialPlanning import MaterialPlanning
import time


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
        if time.time() - last_updated > 60 * 60 * 12:
            mp.update()
            last_updated = time.time()
        dct = mp.get_plan(required_dct, owned_dct, False)
    except ValueError as e:
        return response.json({"error": True, "reason": str(e)})

    return response.json(dct)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
