function checkAll(field)
{
    for (i = 0; i < field.length; i++){
        field[i].checked = true;
    }
}

function uncheckAll(field)
{
    for (i = 0; i < field.length; i++){
        field[i].checked = false;
    }
}

function blink(tag)
{
    tag.style['background-color'] = 'red';
}

function checkFormValue(form)
{
    var value = +form.value;
    form.style["background-color"] = "white";
    if (value >= 0 && value <= 2400 && form.value != ""){
        return true;
    } else{
        setTimeout(function() { blink(form); }, 150)
        return false;
    }
}
