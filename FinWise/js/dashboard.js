/* =========================================
   FINWISE DASHBOARD JAVASCRIPT
========================================= */


document.addEventListener("DOMContentLoaded", () => {


    const sidebar =
        document.getElementById("sidebar");


    const mobileMenu =
        document.getElementById("mobileMenu");


    const newChatButton =
        document.getElementById(
            "newChatButton"
        );


    /* =====================================
       MOBILE SIDEBAR
    ====================================== */

    if (mobileMenu) {

        mobileMenu.addEventListener(
            "click",
            () => {

                sidebar.classList.toggle(
                    "open"
                );

            }
        );

    }


    /* =====================================
       NEW CHAT
    ====================================== */

    if (newChatButton) {

        newChatButton.addEventListener(
            "click",
            () => {

                window.location.reload();

            }
        );

    }


    /* =====================================
       SIDEBAR CONVERSATIONS
    ====================================== */

    const conversations =
        document.querySelectorAll(
            ".conversation"
        );


    conversations.forEach(
        (conversation) => {

            conversation.addEventListener(
                "click",
                () => {

                    conversations.forEach(
                        (item) => {

                            item.classList.remove(
                                "active"
                            );

                        }
                    );


                    conversation.classList.add(
                        "active"
                    );


                    /*
                        Later this will load
                        the selected conversation
                        from the backend.
                    */

                }
            );

        }
    );

});